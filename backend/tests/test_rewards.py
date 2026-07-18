"""
Tests for /rewards/* and the admin manual-adjustment integration.
"""
import pytest
from bson import ObjectId


class TestRewardBalance:
    async def test_new_user_starts_at_zero_silver(self, client, customer):
        resp = await client.get("/rewards", headers=customer["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["total_points"] == 0
        assert resp.json()["data"]["current_tier"] == "Silver"

    async def test_tiers_endpoint_no_auth_required(self, client):
        resp = await client.get("/rewards/tiers")
        assert resp.status_code == 200
        assert len(resp.json()["data"]["tiers"]) == 3


class TestRedeem:
    async def test_redeem_below_minimum_rejected(self, client, customer, product):
        await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
        resp = await client.post("/rewards/redeem", headers=customer["headers"], json={"points": 10})
        assert resp.status_code == 400

    async def test_redeem_more_than_balance_rejected(self, client, customer, product, db):
        await db.rewards.update_one({"user_id": customer["id"]}, {"$set": {"total_points": 50}})
        await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 5})
        resp = await client.post("/rewards/redeem", headers=customer["headers"], json={"points": 500})
        assert resp.status_code == 400

    async def test_redeem_over_max_percent_of_order_rejected(self, client, customer, product, db):
        await db.rewards.update_one({"user_id": customer["id"]}, {"$set": {"total_points": 1000}})
        await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
        # product is ₹599, max redeemable is 50% = ~299 points, requesting way more
        resp = await client.post("/rewards/redeem", headers=customer["headers"], json={"points": 500})
        assert resp.status_code == 400

    async def test_redeem_success_reflected_in_cart_summary(self, client, customer, product, db):
        await db.rewards.update_one({"user_id": customer["id"]}, {"$set": {"total_points": 1000}})
        await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
        resp = await client.post("/rewards/redeem", headers=customer["headers"], json={"points": 150})
        assert resp.status_code == 200

        summary = await client.get("/cart/summary", headers=customer["headers"])
        assert summary.json()["data"].get("redeemed_points") == 150

    async def test_redeem_is_held_not_deducted_until_order_placed(self, client, customer, product, db):
        """Balance should NOT decrease immediately on redeem — only on actual order placement."""
        await db.rewards.update_one({"user_id": customer["id"]}, {"$set": {"total_points": 1000}})
        await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
        await client.post("/rewards/redeem", headers=customer["headers"], json={"points": 150})

        balance = await client.get("/rewards", headers=customer["headers"])
        assert balance.json()["data"]["total_points"] == 1000   # unchanged so far

    async def test_redeem_deducted_after_order_placement(self, client, customer, product, address, db):
        await db.rewards.update_one({"user_id": customer["id"]}, {"$set": {"total_points": 1000}})
        await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
        await client.post("/rewards/redeem", headers=customer["headers"], json={"points": 150})
        await client.post("/orders", headers=customer["headers"], json={"address_id": address, "payment_method": "cod"})

        balance = await client.get("/rewards", headers=customer["headers"])
        assert balance.json()["data"]["total_points"] == 850

    async def test_transaction_recorded_after_redemption_commit(self, client, customer, product, address, db):
        await db.rewards.update_one({"user_id": customer["id"]}, {"$set": {"total_points": 1000}})
        await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
        await client.post("/rewards/redeem", headers=customer["headers"], json={"points": 150})
        await client.post("/orders", headers=customer["headers"], json={"address_id": address, "payment_method": "cod"})

        txns = await client.get("/rewards/transactions", headers=customer["headers"])
        types = [t["type"] for t in txns.json()["data"]["items"]]
        assert "redeem" in types


class TestAdminRewardAdjustment:
    async def test_admin_add_points(self, client, admin, customer):
        resp = await client.post(f"/admin/customers/{customer['id']}/reward", headers=admin["headers"],
                                  json={"points": 200, "reason": "Goodwill gesture"})
        assert resp.status_code == 200
        assert resp.json()["data"]["new_balance"] == 200

    async def test_admin_deduct_more_than_balance_rejected(self, client, admin, customer):
        resp = await client.post(f"/admin/customers/{customer['id']}/reward", headers=admin["headers"],
                                  json={"points": -100, "reason": "Correction"})
        assert resp.status_code == 400

    async def test_admin_adjustment_appears_in_customer_transaction_history(self, client, admin, customer):
        await client.post(f"/admin/customers/{customer['id']}/reward", headers=admin["headers"],
                           json={"points": 300, "reason": "Compensation for late delivery"})
        txns = await client.get("/rewards/transactions", headers=customer["headers"])
        descriptions = [t["description"] for t in txns.json()["data"]["items"]]
        assert any("adjustment" in d.lower() or "compensation" in d.lower() for d in descriptions)

    async def test_zero_points_adjustment_rejected(self, client, admin, customer):
        resp = await client.post(f"/admin/customers/{customer['id']}/reward", headers=admin["headers"],
                                  json={"points": 0, "reason": "test"})
        assert resp.status_code == 422

    async def test_positive_adjustment_counts_toward_lifetime_points(self, client, admin, customer, db):
        await client.post(f"/admin/customers/{customer['id']}/reward", headers=admin["headers"],
                           json={"points": 1200, "reason": "Bulk correction"})
        reward = await db.rewards.find_one({"user_id": customer["id"]})
        assert reward["lifetime_points"] >= 1200

        balance = await client.get("/rewards", headers=customer["headers"])
        assert balance.json()["data"]["current_tier"] == "Gold"