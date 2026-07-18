"""
Tests for /admin/customers/*.
"""
import pytest


async def _place_order(client, customer, product, address):
    await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
    resp = await client.post("/orders", headers=customer["headers"], json={"address_id": address, "payment_method": "cod"})
    return resp.json()["data"]["id"]


class TestListCustomers:
    async def test_total_spend_excludes_cancelled(self, client, admin, customer, product, address):
        order_id = await _place_order(client, customer, product, address)
        before = await client.get("/admin/customers", headers=admin["headers"])
        row_before = next(c for c in before.json()["data"]["items"] if c["id"] == customer["id"])

        await client.put(f"/admin/orders/{order_id}/status", headers=admin["headers"], json={"status": "cancelled"})

        after = await client.get("/admin/customers", headers=admin["headers"])
        row_after = next(c for c in after.json()["data"]["items"] if c["id"] == customer["id"])
        assert row_after["total_spend"] == row_before["total_spend"] - product["price"]

    async def test_search_by_name(self, client, admin, customer, db):
        from bson import ObjectId
        user = await db.users.find_one({"_id": ObjectId(customer["id"])})
        resp = await client.get(f"/admin/customers?search={user['name'][:4]}", headers=admin["headers"])
        assert resp.status_code == 200
        assert any(c["id"] == customer["id"] for c in resp.json()["data"]["items"])


class TestCustomerDetail:
    async def test_avg_order_value_computed(self, client, admin, customer, product, address):
        await _place_order(client, customer, product, address)
        resp = await client.get(f"/admin/customers/{customer['id']}", headers=admin["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["avg_order_value"] == product["price"]

    async def test_loyalty_tier_matches_lifetime_points(self, client, admin, customer, db):
        await db.rewards.update_one({"user_id": customer["id"]}, {"$set": {"lifetime_points": 6000}})
        resp = await client.get(f"/admin/customers/{customer['id']}", headers=admin["headers"])
        assert resp.json()["data"]["loyalty_tier"] == "Platinum"

    async def test_nonexistent_customer_404(self, client, admin):
        resp = await client.get("/admin/customers/000000000000000000000000", headers=admin["headers"])
        assert resp.status_code == 404


class TestBlockUnblock:
    async def test_block_toggles_is_active(self, client, admin, customer):
        resp = await client.put(f"/admin/customers/{customer['id']}/block", headers=admin["headers"], json={"reason": "Fraud suspicion"})
        assert resp.status_code == 200
        assert resp.json()["data"]["is_active"] is False

    async def test_unblock_toggles_back(self, client, admin, customer):
        await client.put(f"/admin/customers/{customer['id']}/block", headers=admin["headers"], json={})
        resp = await client.put(f"/admin/customers/{customer['id']}/block", headers=admin["headers"], json={})
        assert resp.json()["data"]["is_active"] is True

    async def test_blocked_customer_access_token_rejected_on_next_request(self, client, admin, customer):
        """
        Depends on get_current_user checking is_active — regression test for
        the exact gap flagged when the customers admin module was built.
        """
        await client.put(f"/admin/customers/{customer['id']}/block", headers=admin["headers"], json={})
        resp = await client.get("/users/profile", headers=customer["headers"])
        assert resp.status_code == 401

    async def test_customer_cannot_block_themselves_via_this_route(self, client, customer):
        resp = await client.put(f"/admin/customers/{customer['id']}/block", headers=customer["headers"], json={})
        assert resp.status_code == 403


class TestAdminRewardAdjustmentIntegration:
    async def test_deduction_cannot_exceed_balance(self, client, admin, customer, db):
        await db.rewards.update_one({"user_id": customer["id"]}, {"$set": {"total_points": 50}})
        resp = await client.post(f"/admin/customers/{customer['id']}/reward", headers=admin["headers"],
                                  json={"points": -100, "reason": "test"})
        assert resp.status_code == 400

    async def test_reward_adjustment_requires_reason(self, client, admin, customer):
        resp = await client.post(f"/admin/customers/{customer['id']}/reward", headers=admin["headers"],
                                  json={"points": 100, "reason": "x"})
        assert resp.status_code == 422