"""
Tests for /users/* — profile, password change, address management.
"""
import pytest


class TestProfile:
    async def test_get_profile_no_password_hash(self, client, customer):
        resp = await client.get("/users/profile", headers=customer["headers"])
        assert resp.status_code == 200
        assert "password_hash" not in resp.json()["data"]

    async def test_update_profile_name_and_phone(self, client, customer):
        resp = await client.put("/users/profile", headers=customer["headers"],
                                 json={"name": "Updated Name", "phone": "9123456780"})
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Updated Name"

    async def test_update_profile_no_fields_rejected(self, client, customer):
        resp = await client.put("/users/profile", headers=customer["headers"], json={})
        assert resp.status_code == 400

    async def test_update_profile_email_taken_by_another_user_rejected(self, client, customer, second_customer, db):
        second_user = await db.users.find_one({"email": {"$regex": "test.com"}})
        # ensure the two customers have distinct emails, then attempt to steal one
        c1 = await db.users.find_one({})
        others = await db.users.find({"_id": {"$ne": c1["_id"]}}).to_list(length=10)
        assert others, "second_customer fixture should have created a distinct user"
        taken_email = others[0]["email"]

        resp = await client.put("/users/profile", headers=customer["headers"], json={"email": taken_email})
        assert resp.status_code == 409

    async def test_update_profile_same_email_no_conflict(self, client, customer, db):
        me = await client.get("/users/profile", headers=customer["headers"])
        own_email = me.json()["data"]["email"]
        resp = await client.put("/users/profile", headers=customer["headers"], json={"email": own_email})
        assert resp.status_code == 200


class TestChangePassword:
    async def test_change_password_wrong_current_rejected(self, client, customer):
        resp = await client.put("/users/password", headers=customer["headers"], json={
            "current_password": "WrongOne", "new_password": "NewSecurePass456",
        })
        assert resp.status_code in (400, 401)

    async def test_change_password_success_then_old_password_fails_login(self, client, customer, db):
        me = await client.get("/users/profile", headers=customer["headers"])
        email = me.json()["data"]["email"]

        resp = await client.put("/users/password", headers=customer["headers"], json={
            "current_password": "TestPass123", "new_password": "BrandNewPass789",
        })
        assert resp.status_code == 200

        old_login = await client.post("/auth/login", json={"identifier": email, "password": "TestPass123"})
        assert old_login.status_code == 401

        new_login = await client.post("/auth/login", json={"identifier": email, "password": "BrandNewPass789"})
        assert new_login.status_code == 200


class TestAddresses:
    async def test_add_first_address_becomes_default(self, client, customer):
        resp = await client.post("/users/addresses", headers=customer["headers"], json={
            "full_name": "Test User", "phone": "9876543210", "address_line1": "123 Main St",
            "city": "Jabalpur", "state": "MP", "postal_code": "482001",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["is_default"] is True

    async def test_add_second_address_not_default(self, client, customer):
        await client.post("/users/addresses", headers=customer["headers"], json={
            "full_name": "A", "phone": "9876543210", "address_line1": "123 Main St",
            "city": "Jabalpur", "state": "MP", "postal_code": "482001",
        })
        resp = await client.post("/users/addresses", headers=customer["headers"], json={
            "full_name": "B", "phone": "9876543211", "address_line1": "456 Second St",
            "city": "Jabalpur", "state": "MP", "postal_code": "482002",
        })
        assert resp.json()["data"]["is_default"] is False

    async def test_list_addresses_empty_for_new_user(self, client, customer):
        resp = await client.get("/users/addresses", headers=customer["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    async def test_update_nonexistent_address_404(self, client, customer):
        resp = await client.put("/users/addresses/does-not-exist", headers=customer["headers"], json={
            "full_name": "X", "phone": "9876543210", "address_line1": "x",
            "city": "x", "state": "x", "postal_code": "482001",
        })
        assert resp.status_code == 404

    async def test_delete_default_address_promotes_another(self, client, customer):
        first = await client.post("/users/addresses", headers=customer["headers"], json={
            "full_name": "A", "phone": "9876543210", "address_line1": "123 Main St",
            "city": "Jabalpur", "state": "MP", "postal_code": "482001",
        })
        second = await client.post("/users/addresses", headers=customer["headers"], json={
            "full_name": "B", "phone": "9876543211", "address_line1": "456 Second St",
            "city": "Jabalpur", "state": "MP", "postal_code": "482002",
        })
        first_id = first.json()["data"]["id"]
        second_id = second.json()["data"]["id"]

        await client.delete(f"/users/addresses/{first_id}", headers=customer["headers"])

        listing = await client.get("/users/addresses", headers=customer["headers"])
        remaining = listing.json()["data"]
        assert len(remaining) == 1
        assert remaining[0]["id"] == second_id
        assert remaining[0]["is_default"] is True

    async def test_set_default_unsets_previous_default(self, client, customer):
        first = await client.post("/users/addresses", headers=customer["headers"], json={
            "full_name": "A", "phone": "9876543210", "address_line1": "123 Main St",
            "city": "Jabalpur", "state": "MP", "postal_code": "482001",
        })
        second = await client.post("/users/addresses", headers=customer["headers"], json={
            "full_name": "B", "phone": "9876543211", "address_line1": "456 Second St",
            "city": "Jabalpur", "state": "MP", "postal_code": "482002",
        })
        second_id = second.json()["data"]["id"]

        await client.put(f"/users/addresses/{second_id}/default", headers=customer["headers"])

        listing = await client.get("/users/addresses", headers=customer["headers"])
        defaults = [a for a in listing.json()["data"] if a["is_default"]]
        assert len(defaults) == 1
        assert defaults[0]["id"] == second_id

    async def test_cannot_edit_address_belonging_to_another_user(self, client, customer, second_customer):
        """IDOR check: address ids aren't globally unique/guessable-safe by themselves —
        the service must scope every address lookup by the authenticated user_id."""
        created = await client.post("/users/addresses", headers=customer["headers"], json={
            "full_name": "A", "phone": "9876543210", "address_line1": "123 Main St",
            "city": "Jabalpur", "state": "MP", "postal_code": "482001",
        })
        address_id = created.json()["data"]["id"]

        resp = await client.put(f"/users/addresses/{address_id}", headers=second_customer["headers"], json={
            "full_name": "Hijacked", "phone": "9000000000", "address_line1": "x",
            "city": "x", "state": "x", "postal_code": "000000",
        })
        assert resp.status_code == 404