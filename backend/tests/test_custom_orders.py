"""
Tests for /custom-orders/* (customer) and /admin/custom-orders/* (admin).

Covers the full quote lifecycle: pending -> reviewing -> quoted -> confirmed,
plus the customer-facing accept-quote endpoint that closes the loop.
"""
import pytest
from datetime import datetime, timedelta


def _future_datetime(hours=72):
    return (datetime.utcnow() + timedelta(hours=hours)).isoformat()


class TestSubmitCustomOrder:
    async def test_submit_success(self, client, customer):
        resp = await client.post("/custom-orders", headers=customer["headers"], json={
            "occasion": "birthday", "flavor": "chocolate", "size": "2kg",
            "description": "Need a unicorn-themed cake with edible glitter please",
            "needed_by": _future_datetime(72), "contact_phone": "9876543210",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "pending"

    async def test_submit_with_insufficient_lead_time_rejected(self, client, customer):
        resp = await client.post("/custom-orders", headers=customer["headers"], json={
            "occasion": "birthday", "flavor": "vanilla", "size": "1kg",
            "description": "Need this cake super urgently please help",
            "needed_by": _future_datetime(hours=5), "contact_phone": "9876543210",
        })
        assert resp.status_code == 422

    async def test_submit_budget_max_below_min_rejected(self, client, customer):
        resp = await client.post("/custom-orders", headers=customer["headers"], json={
            "occasion": "wedding", "flavor": "vanilla", "size": "5kg",
            "description": "Elaborate multi-tier wedding cake with sugar flowers",
            "needed_by": _future_datetime(72), "contact_phone": "9876543210",
            "budget_min": 5000, "budget_max": 2000,
        })
        assert resp.status_code == 422

    async def test_submit_too_many_reference_images_rejected(self, client, customer):
        resp = await client.post("/custom-orders", headers=customer["headers"], json={
            "occasion": "birthday", "flavor": "chocolate", "size": "1kg",
            "description": "Cake matching one of these reference photos please",
            "needed_by": _future_datetime(72), "contact_phone": "9876543210",
            "reference_images": [f"https://x.com/{i}.jpg" for i in range(6)],
        })
        assert resp.status_code == 422

    async def test_submit_short_description_rejected(self, client, customer):
        resp = await client.post("/custom-orders", headers=customer["headers"], json={
            "occasion": "birthday", "flavor": "chocolate", "size": "1kg",
            "description": "cake", "needed_by": _future_datetime(72), "contact_phone": "9876543210",
        })
        assert resp.status_code == 422


class TestListAndOwnership:
    async def test_list_returns_only_own_requests(self, client, customer, second_customer):
        await client.post("/custom-orders", headers=customer["headers"], json={
            "occasion": "birthday", "flavor": "chocolate", "size": "1kg",
            "description": "Simple chocolate cake for a small gathering",
            "needed_by": _future_datetime(72), "contact_phone": "9876543210",
        })
        resp = await client.get("/custom-orders", headers=second_customer["headers"])
        assert resp.json()["data"]["meta"]["total"] == 0

    async def test_get_detail_cross_user_404(self, client, customer, second_customer):
        created = await client.post("/custom-orders", headers=customer["headers"], json={
            "occasion": "birthday", "flavor": "chocolate", "size": "1kg",
            "description": "Simple chocolate cake for a small gathering",
            "needed_by": _future_datetime(72), "contact_phone": "9876543210",
        })
        request_id = created.json()["data"]["id"]
        resp = await client.get(f"/custom-orders/{request_id}", headers=second_customer["headers"])
        assert resp.status_code == 404


class TestAdminQuotingLifecycle:
    async def _submit(self, client, customer):
        resp = await client.post("/custom-orders", headers=customer["headers"], json={
            "occasion": "wedding", "flavor": "red velvet", "size": "3kg",
            "description": "Three-tier wedding cake, white and gold theme please",
            "needed_by": _future_datetime(72), "contact_phone": "9876543210",
        })
        return resp.json()["data"]["id"]

    async def test_move_to_reviewing(self, client, admin, customer):
        request_id = await self._submit(client, customer)
        resp = await client.put(f"/admin/custom-orders/{request_id}/status", headers=admin["headers"],
                                 json={"status": "reviewing"})
        assert resp.status_code == 200

    async def test_set_quote_while_pending_succeeds(self, client, admin, customer):
        request_id = await self._submit(client, customer)
        resp = await client.post(f"/admin/custom-orders/{request_id}/quote", headers=admin["headers"],
                                  json={"quoted_price": 3500})
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "quoted"
        assert resp.json()["data"]["quoted_price"] == 3500

    async def test_set_quote_while_confirmed_rejected(self, client, admin, customer, db):
        from bson import ObjectId
        request_id = await self._submit(client, customer)
        await client.post(f"/admin/custom-orders/{request_id}/quote", headers=admin["headers"],
                           json={"quoted_price": 3500})
        await db.custom_orders.update_one({"_id": ObjectId(request_id)}, {"$set": {"status": "confirmed"}})

        resp = await client.post(f"/admin/custom-orders/{request_id}/quote", headers=admin["headers"],
                                  json={"quoted_price": 4000})
        assert resp.status_code == 400

    async def test_confirm_without_quote_rejected(self, client, admin, customer, db):
        from bson import ObjectId
        request_id = await self._submit(client, customer)
        await client.put(f"/admin/custom-orders/{request_id}/status", headers=admin["headers"],
                          json={"status": "reviewing"})
        # attempt to force straight to confirmed without ever quoting
        resp = await client.put(f"/admin/custom-orders/{request_id}/status", headers=admin["headers"],
                                 json={"status": "confirmed"})
        assert resp.status_code == 400

    async def test_illegal_transition_skipping_confirmed_rejected(self, client, admin, customer):
        request_id = await self._submit(client, customer)
        await client.post(f"/admin/custom-orders/{request_id}/quote", headers=admin["headers"],
                           json={"quoted_price": 3500})
        resp = await client.put(f"/admin/custom-orders/{request_id}/status", headers=admin["headers"],
                                 json={"status": "in_progress"})
        assert resp.status_code == 400

    async def test_zero_or_negative_quote_rejected(self, client, admin, customer):
        request_id = await self._submit(client, customer)
        resp = await client.post(f"/admin/custom-orders/{request_id}/quote", headers=admin["headers"],
                                  json={"quoted_price": 0})
        assert resp.status_code == 422


class TestAcceptQuote:
    async def _submit_and_quote(self, client, admin, customer):
        submitted = await client.post("/custom-orders", headers=customer["headers"], json={
            "occasion": "birthday", "flavor": "chocolate", "size": "2kg",
            "description": "Simple chocolate birthday cake with candles",
            "needed_by": _future_datetime(72), "contact_phone": "9876543210",
        })
        request_id = submitted.json()["data"]["id"]
        await client.post(f"/admin/custom-orders/{request_id}/quote", headers=admin["headers"],
                           json={"quoted_price": 1200})
        return request_id

    async def test_accept_quote_success(self, client, admin, customer):
        request_id = await self._submit_and_quote(client, admin, customer)
        resp = await client.post(f"/custom-orders/{request_id}/accept-quote", headers=customer["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "confirmed"

    async def test_accept_quote_when_not_quoted_rejected(self, client, customer):
        submitted = await client.post("/custom-orders", headers=customer["headers"], json={
            "occasion": "birthday", "flavor": "chocolate", "size": "1kg",
            "description": "Simple chocolate birthday cake, nothing fancy",
            "needed_by": _future_datetime(72), "contact_phone": "9876543210",
        })
        request_id = submitted.json()["data"]["id"]
        resp = await client.post(f"/custom-orders/{request_id}/accept-quote", headers=customer["headers"])
        assert resp.status_code == 400

    async def test_accept_quote_cross_user_404(self, client, admin, customer, second_customer):
        request_id = await self._submit_and_quote(client, admin, customer)
        resp = await client.post(f"/custom-orders/{request_id}/accept-quote", headers=second_customer["headers"])
        assert resp.status_code == 404