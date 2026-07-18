"""
Tests for /notifications/* — in-app notification history, read/unread state,
channel preferences, and the integration hook from order placement.
"""
import pytest


class TestNotificationHistory:
    async def test_placing_order_creates_notification(self, client, customer, product, address):
        await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
        await client.post("/orders", headers=customer["headers"], json={"address_id": address, "payment_method": "cod"})

        resp = await client.get("/notifications", headers=customer["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["unread_count"] >= 1
        assert any(n["type"] == "order_placed" for n in resp.json()["data"]["items"])

    async def test_unread_count_accurate(self, client, customer, product, address):
        await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
        await client.post("/orders", headers=customer["headers"], json={"address_id": address, "payment_method": "cod"})

        listing = await client.get("/notifications", headers=customer["headers"])
        data = listing.json()["data"]
        actual_unread = sum(1 for n in data["items"] if not n["is_read"])
        assert data["unread_count"] == actual_unread


class TestMarkRead:
    async def test_mark_single_notification_read(self, client, customer, product, address):
        await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
        await client.post("/orders", headers=customer["headers"], json={"address_id": address, "payment_method": "cod"})

        listing = await client.get("/notifications", headers=customer["headers"])
        notif_id = listing.json()["data"]["items"][0]["id"]

        resp = await client.put(f"/notifications/{notif_id}/read", headers=customer["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["is_read"] is True

    async def test_mark_read_cross_user_404(self, client, customer, second_customer, product, address):
        await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
        await client.post("/orders", headers=customer["headers"], json={"address_id": address, "payment_method": "cod"})

        listing = await client.get("/notifications", headers=customer["headers"])
        notif_id = listing.json()["data"]["items"][0]["id"]

        resp = await client.put(f"/notifications/{notif_id}/read", headers=second_customer["headers"])
        assert resp.status_code == 404

    async def test_mark_nonexistent_notification_404(self, client, customer):
        resp = await client.put("/notifications/000000000000000000000000/read", headers=customer["headers"])
        assert resp.status_code == 404

    async def test_mark_all_read(self, client, customer, product, address):
        await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
        await client.post("/orders", headers=customer["headers"], json={"address_id": address, "payment_method": "cod"})

        resp = await client.put("/notifications/read-all", headers=customer["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["marked_read"] >= 1

        listing = await client.get("/notifications", headers=customer["headers"])
        assert listing.json()["data"]["unread_count"] == 0


class TestPreferences:
    async def test_default_preferences_for_new_user(self, client, customer):
        resp = await client.get("/notifications/preferences", headers=customer["headers"])
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data == {"email": True, "sms": True, "whatsapp": False}

    async def test_partial_update_does_not_clobber_other_channels(self, client, customer):
        resp = await client.put("/notifications/preferences", headers=customer["headers"], json={"sms": False})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["sms"] is False
        assert data["email"] is True    # untouched
        assert data["whatsapp"] is False  # untouched

    async def test_preferences_persist_across_requests(self, client, customer):
        await client.put("/notifications/preferences", headers=customer["headers"], json={"whatsapp": True})
        resp = await client.get("/notifications/preferences", headers=customer["headers"])
        assert resp.json()["data"]["whatsapp"] is True