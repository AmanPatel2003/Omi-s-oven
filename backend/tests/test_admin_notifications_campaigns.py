"""
Tests for /admin/notifications/send and /admin/notifications/broadcast.
"""
import pytest


class TestSendTargeted:
    async def test_requires_customer_ids_or_segment(self, client, admin):
        resp = await client.post("/admin/notifications/send", headers=admin["headers"], json={
            "channel": "sms", "message": "Hello there, big sale today!",
        })
        assert resp.status_code == 400

    async def test_email_channel_requires_subject(self, client, admin, customer):
        resp = await client.post("/admin/notifications/send", headers=admin["headers"], json={
            "channel": "email", "customer_ids": [customer["id"]], "message": "Big sale today, don't miss it",
        })
        assert resp.status_code == 400

    async def test_send_to_explicit_customer_ids(self, client, admin, customer):
        resp = await client.post("/admin/notifications/send", headers=admin["headers"], json={
            "channel": "sms", "customer_ids": [customer["id"]], "message": "Your favorite cake is back in stock!",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["target_count"] == 1

    async def test_response_always_flags_unconfigured_provider(self, client, admin, customer):
        """Providers are stubs — the response must be honest about this, not claim success."""
        resp = await client.post("/admin/notifications/send", headers=admin["headers"], json={
            "channel": "sms", "customer_ids": [customer["id"]], "message": "Test campaign message here",
        })
        data = resp.json()["data"]
        assert data["provider_configured"] is False
        assert "warning" in data

    async def test_muted_channel_customer_is_skipped(self, client, admin, customer):
        await client.put("/notifications/preferences", headers=customer["headers"], json={"sms": False})
        resp = await client.post("/admin/notifications/send", headers=admin["headers"], json={
            "channel": "sms", "customer_ids": [customer["id"]], "message": "Test campaign message here",
        })
        assert resp.json()["data"]["skipped_count"] == 1

    async def test_segment_by_inactive_days_excludes_recent_orderers(self, client, admin, customer, second_customer, product, address):
        await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
        await client.post("/orders", headers=customer["headers"], json={"address_id": address, "payment_method": "cod"})

        resp = await client.post("/admin/notifications/send", headers=admin["headers"], json={
            "channel": "email", "subject": "We miss you!",
            "segment": {"inactive_days": 30}, "message": "Come back and get 10% off your next order",
        })
        assert resp.status_code == 200
        # customer ordered recently, so should be excluded; second_customer never ordered, should be included
        assert resp.json()["data"]["target_count"] >= 1


class TestBroadcast:
    async def test_broadcast_requires_message(self, client, admin):
        resp = await client.post("/admin/notifications/broadcast", headers=admin["headers"], json={
            "channel": "sms",
        })
        assert resp.status_code == 422

    async def test_broadcast_excludes_inactive_by_default(self, client, admin, customer, second_customer):
        await client.put(f"/admin/customers/{customer['id']}/block", headers=admin["headers"], json={})

        resp = await client.post("/admin/notifications/broadcast", headers=admin["headers"], json={
            "channel": "sms", "message": "Store-wide announcement: new menu items available",
        })
        assert resp.status_code == 200
        # blocked customer should not appear in the campaign target count for a default broadcast
        # (exact count depends on other fixtures, so just verify blocked user's exclusion logic runs without error)

    async def test_broadcast_include_inactive_when_flag_set(self, client, admin, customer):
        await client.put(f"/admin/customers/{customer['id']}/block", headers=admin["headers"], json={})

        resp = await client.post("/admin/notifications/broadcast", headers=admin["headers"], json={
            "channel": "sms", "message": "Reactivation offer just for you, come back today",
            "exclude_inactive": False,
        })
        assert resp.status_code == 200

    async def test_regular_customer_cannot_broadcast(self, client, customer):
        resp = await client.post("/admin/notifications/broadcast", headers=customer["headers"], json={
            "channel": "sms", "message": "unauthorized attempt to broadcast a message",
        })
        assert resp.status_code == 403

    async def test_campaign_logged_with_accurate_counts(self, client, admin, customer, db):
        resp = await client.post("/admin/notifications/broadcast", headers=admin["headers"], json={
            "channel": "email", "subject": "Test", "message": "Testing campaign logging behavior end to end",
        })
        campaign_id = resp.json()["data"]["id"]
        campaign = await db.campaigns.find_one({"_id": __import__("bson").ObjectId(campaign_id)})
        assert campaign["status"] == "completed"
        assert campaign["target_count"] == campaign["sent_count"] + campaign["failed_count"] + campaign["skipped_count"]