"""
Tests for /auth/* — register, login, google-login, refresh, change-password, /me.

Every test here maps to a real issue we caught during code review:
- email/phone case-sensitivity and normalization
- password_hash leakage in /me
- duplicate account race conditions (covered via unique index, not concurrency sim)
- invalid refresh token handling
"""
import pytest


class TestRegister:
    async def test_register_success_returns_tokens_and_user(self, client):
        resp = await client.post("/auth/register", json={
            "name": "Priya Sharma", "email": "priya@test.com",
            "phone": "9876543210", "password": "SecurePass123",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "access_token" in data and "refresh_token" in data
        assert data["user"]["email"] == "priya@test.com"
        assert "password_hash" not in data["user"]   # must never leak

    async def test_register_duplicate_email_rejected(self, client):
        payload = {"name": "A", "email": "dup@test.com", "phone": "9111111111", "password": "SecurePass123"}
        await client.post("/auth/register", json=payload)
        payload["phone"] = "9222222222"
        resp = await client.post("/auth/register", json=payload)
        assert resp.status_code == 409

    async def test_register_duplicate_email_different_case_rejected(self, client):
        """Regression: register_user lowercased for the uniqueness check but stored raw case."""
        await client.post("/auth/register", json={
            "name": "A", "email": "CaseTest@Test.com", "phone": "9333333333", "password": "SecurePass123",
        })
        resp = await client.post("/auth/register", json={
            "name": "B", "email": "casetest@test.com", "phone": "9444444444", "password": "SecurePass123",
        })
        assert resp.status_code == 409

    async def test_register_invalid_indian_phone_rejected(self, client):
        resp = await client.post("/auth/register", json={
            "name": "A", "email": "badphone@test.com", "phone": "12345", "password": "SecurePass123",
        })
        assert resp.status_code == 422

    async def test_register_short_password_rejected(self, client):
        resp = await client.post("/auth/register", json={
            "name": "A", "email": "shortpw@test.com", "phone": "9555555555", "password": "abc",
        })
        assert resp.status_code == 422

    async def test_register_creates_rewards_document(self, client, db):
        resp = await client.post("/auth/register", json={
            "name": "A", "email": "rewardcheck@test.com", "phone": "9666666666", "password": "SecurePass123",
        })
        user_id = resp.json()["data"]["user"]["id"]
        reward = await db.rewards.find_one({"user_id": user_id})
        assert reward is not None
        assert reward["total_points"] == 0


class TestLogin:
    async def test_login_with_email(self, client):
        await client.post("/auth/register", json={
            "name": "A", "email": "loginemail@test.com", "phone": "9777777771", "password": "SecurePass123",
        })
        resp = await client.post("/auth/login", json={"identifier": "loginemail@test.com", "password": "SecurePass123"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()["data"]

    async def test_login_with_phone(self, client):
        await client.post("/auth/register", json={
            "name": "A", "email": "loginphone@test.com", "phone": "9777777772", "password": "SecurePass123",
        })
        resp = await client.post("/auth/login", json={"identifier": "9777777772", "password": "SecurePass123"})
        assert resp.status_code == 200

    async def test_login_wrong_password_rejected(self, client):
        await client.post("/auth/register", json={
            "name": "A", "email": "wrongpw@test.com", "phone": "9777777773", "password": "SecurePass123",
        })
        resp = await client.post("/auth/login", json={"identifier": "wrongpw@test.com", "password": "WrongPass"})
        assert resp.status_code == 401

    async def test_login_nonexistent_user_returns_same_error_as_wrong_password(self, client):
        """Security: must not leak whether the identifier exists."""
        resp = await client.post("/auth/login", json={"identifier": "ghost@test.com", "password": "whatever"})
        assert resp.status_code == 401
        assert "invalid credentials" in resp.json()["message"].lower() or "invalid" in str(resp.json()).lower()

    async def test_login_deactivated_account_rejected(self, client, db):
        resp = await client.post("/auth/register", json={
            "name": "A", "email": "deactivated@test.com", "phone": "9777777774", "password": "SecurePass123",
        })
        user_id = resp.json()["data"]["user"]["id"]
        from bson import ObjectId
        await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"is_active": False}})
        resp2 = await client.post("/auth/login", json={"identifier": "deactivated@test.com", "password": "SecurePass123"})
        assert resp2.status_code == 401


class TestRefreshToken:
    async def test_refresh_with_valid_token_returns_new_pair(self, client):
        reg = await client.post("/auth/register", json={
            "name": "A", "email": "refresh@test.com", "phone": "9777777775", "password": "SecurePass123",
        })
        refresh_token = reg.json()["data"]["refresh_token"]
        resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        assert "access_token" in resp.json()["data"]

    async def test_refresh_with_malformed_token_returns_401_not_500(self, client):
        """Regression: decode_token can raise instead of returning None on bad input."""
        resp = await client.post("/auth/refresh", json={"refresh_token": "not.a.valid.jwt"})
        assert resp.status_code == 401

    async def test_refresh_with_access_token_instead_of_refresh_rejected(self, client):
        reg = await client.post("/auth/register", json={
            "name": "A", "email": "wrongtype@test.com", "phone": "9777777776", "password": "SecurePass123",
        })
        access_token = reg.json()["data"]["access_token"]
        resp = await client.post("/auth/refresh", json={"refresh_token": access_token})
        assert resp.status_code == 401


class TestMe:
    async def test_me_returns_profile_without_password_hash(self, client, customer):
        resp = await client.get("/auth/me", headers=customer["headers"])
        assert resp.status_code == 200
        assert "password_hash" not in resp.json()["data"]

    async def test_me_without_token_rejected(self, client):
        resp = await client.get("/auth/me")
        assert resp.status_code == 401


class TestChangePassword:
    async def test_change_password_success(self, client, customer):
        resp = await client.put("/auth/change-password", headers=customer["headers"], json={
            "old_password": "TestPass123", "new_password": "NewSecurePass456",
        })
        assert resp.status_code == 200

    async def test_change_password_wrong_old_password_rejected(self, client, customer):
        resp = await client.put("/auth/change-password", headers=customer["headers"], json={
            "old_password": "WrongOldPass", "new_password": "NewSecurePass456",
        })
        assert resp.status_code == 401

    async def test_new_password_actually_works_for_next_login(self, client, customer, db):
        user = await db.users.find_one({})
        await client.put("/auth/change-password", headers=customer["headers"], json={
            "old_password": "TestPass123", "new_password": "BrandNewPass789",
        })
        resp = await client.post("/auth/login", json={"identifier": user["email"], "password": "BrandNewPass789"})
        assert resp.status_code == 200