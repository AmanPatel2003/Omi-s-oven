"""
Fills the gaps left in test_admin.py: admin order LIST/filter/search/export,
and admin coupon LIST/usage/update/deactivate (only create was covered before).
"""
import pytest
from datetime import datetime, timedelta


async def _place_order(client, customer, product, address):
    await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
    resp = await client.post("/orders", headers=customer["headers"], json={"address_id": address, "payment_method": "cod"})
    return resp.json()["data"]["id"]


class TestAdminOrderListing:
    async def test_filter_by_status(self, client, admin, customer, product, address):
        order_id = await _place_order(client, customer, product, address)
        await client.put(f"/admin/orders/{order_id}/status", headers=admin["headers"], json={"status": "confirmed"})

        resp = await client.get("/admin/orders?status=confirmed", headers=admin["headers"])
        assert resp.status_code == 200
        assert any(o["id"] == order_id for o in resp.json()["data"]["items"])

        resp2 = await client.get("/admin/orders?status=pending", headers=admin["headers"])
        assert not any(o["id"] == order_id for o in resp2.json()["data"]["items"])

    async def test_search_by_order_number(self, client, admin, customer, product, address):
        order_id = await _place_order(client, customer, product, address)
        detail = await client.get(f"/admin/orders/{order_id}", headers=admin["headers"])
        order_number = detail.json()["data"]["order_number"]

        resp = await client.get(f"/admin/orders?search={order_number}", headers=admin["headers"])
        assert any(o["id"] == order_id for o in resp.json()["data"]["items"])

    async def test_search_by_customer_phone(self, client, admin, customer, product, address, db):
        order_id = await _place_order(client, customer, product, address)
        detail = await client.get(f"/admin/orders/{order_id}", headers=admin["headers"])
        phone = detail.json()["data"]["address"]["phone"]

        resp = await client.get(f"/admin/orders?search={phone}", headers=admin["headers"])
        assert any(o["id"] == order_id for o in resp.json()["data"]["items"])

    async def test_date_range_filter(self, client, admin, customer, product, address):
        await _place_order(client, customer, product, address)
        tomorrow = (datetime.utcnow() + timedelta(days=1)).isoformat()
        day_after = (datetime.utcnow() + timedelta(days=2)).isoformat()

        resp = await client.get(f"/admin/orders?date_from={tomorrow}&date_to={day_after}", headers=admin["headers"])
        assert resp.json()["data"]["meta"]["total"] == 0

    async def test_get_order_detail_includes_customer_email(self, client, admin, customer, product, address):
        order_id = await _place_order(client, customer, product, address)
        resp = await client.get(f"/admin/orders/{order_id}", headers=admin["headers"])
        assert resp.status_code == 200
        assert "customer_email" in resp.json()["data"]

    async def test_get_order_shows_assigned_rider_when_present(self, client, admin, delivery_staff, customer, product, address):
        order_id = await _place_order(client, customer, product, address)
        await client.put(f"/admin/orders/{order_id}/status", headers=admin["headers"], json={"status": "confirmed"})
        await client.post(f"/admin/orders/{order_id}/assign-delivery", headers=admin["headers"],
                           json={"rider_id": delivery_staff["id"]})

        resp = await client.get(f"/admin/orders/{order_id}", headers=admin["headers"])
        assert resp.json()["data"]["assigned_rider_id"] == delivery_staff["id"]

    async def test_get_order_no_rider_shows_null(self, client, admin, customer, product, address):
        order_id = await _place_order(client, customer, product, address)
        resp = await client.get(f"/admin/orders/{order_id}", headers=admin["headers"])
        assert resp.json()["data"]["assigned_rider_id"] is None

    async def test_nonexistent_order_404(self, client, admin):
        resp = await client.get("/admin/orders/000000000000000000000000", headers=admin["headers"])
        assert resp.status_code == 404

    async def test_assign_delivery_to_unconfirmed_order_rejected(self, client, admin, delivery_staff, customer, product, address):
        order_id = await _place_order(client, customer, product, address)
        # still "pending" — not confirmed/preparing
        resp = await client.post(f"/admin/orders/{order_id}/assign-delivery", headers=admin["headers"],
                                  json={"rider_id": delivery_staff["id"]})
        assert resp.status_code == 400

    async def test_assign_delivery_to_non_rider_rejected(self, client, admin, customer, second_customer, product, address):
        order_id = await _place_order(client, customer, product, address)
        await client.put(f"/admin/orders/{order_id}/status", headers=admin["headers"], json={"status": "confirmed"})
        # second_customer has role "customer", not "delivery_staff"
        resp = await client.post(f"/admin/orders/{order_id}/assign-delivery", headers=admin["headers"],
                                  json={"rider_id": second_customer["id"]})
        assert resp.status_code == 400


class TestAdminOrderExport:
    async def test_export_returns_csv(self, client, admin, customer, product, address):
        await _place_order(client, customer, product, address)
        resp = await client.get("/admin/orders/export", headers=admin["headers"])
        assert resp.status_code == 200
        assert "csv" in resp.headers["content-type"]
        assert b"Order Number" in resp.content

    async def test_export_route_not_swallowed_by_id_route(self, client, admin):
        """Regression: /admin/orders/export must resolve before /admin/orders/{order_id}."""
        resp = await client.get("/admin/orders/export", headers=admin["headers"])
        assert resp.status_code == 200   # not a 400 from _to_object_id("export") failing

    async def test_export_invalid_date_range_rejected(self, client, admin):
        resp = await client.get(
            "/admin/orders/export?date_from=2026-08-01T00:00:00&date_to=2026-07-01T00:00:00",
            headers=admin["headers"],
        )
        assert resp.status_code == 400

    async def test_export_requires_admin(self, client, customer):
        resp = await client.get("/admin/orders/export", headers=customer["headers"])
        assert resp.status_code == 403


class TestAdminCouponListingAndUsage:
    async def test_list_includes_usage_stats(self, client, admin, coupon):
        resp = await client.get("/admin/coupons", headers=admin["headers"])
        assert resp.status_code == 200
        row = next(c for c in resp.json()["data"] if c["code"] == "SAVE20")
        assert "usage_remaining" in row
        assert "total_discount_given" in row
        assert row["is_expired"] is False

    async def test_update_coupon(self, client, admin, coupon):
        resp = await client.put(f"/admin/coupons/{coupon['_id']}", headers=admin["headers"], json={
            "description": "Updated description",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["description"] == "Updated description"

    async def test_lowering_usage_limit_below_used_count_rejected(self, client, admin, coupon, db):
        await db.coupons.update_one({"_id": coupon["_id"]}, {"$set": {"used_count": 50}})
        resp = await client.put(f"/admin/coupons/{coupon['_id']}", headers=admin["headers"], json={
            "usage_limit": 10,
        })
        assert resp.status_code == 400

    async def test_deactivate_coupon(self, client, admin, coupon):
        resp = await client.delete(f"/admin/coupons/{coupon['_id']}", headers=admin["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["is_active"] is False

    async def test_deactivated_coupon_cannot_be_applied(self, client, admin, customer, coupon, product):
        await client.delete(f"/admin/coupons/{coupon['_id']}", headers=admin["headers"])
        await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
        resp = await client.post("/cart/apply-coupon", headers=customer["headers"], json={"code": "SAVE20"})
        assert resp.status_code == 404

    async def test_usage_history_reflects_real_order(self, client, admin, customer, product, address, coupon):
        await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
        await client.post("/cart/apply-coupon", headers=customer["headers"], json={"code": "SAVE20"})
        await client.post("/orders", headers=customer["headers"], json={"address_id": address, "payment_method": "cod"})

        resp = await client.get(f"/admin/coupons/{coupon['_id']}/usage", headers=admin["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["meta"]["total"] == 1
        assert resp.json()["data"]["items"][0]["user_id"] == customer["id"]

    async def test_usage_history_empty_coupon(self, client, admin, coupon):
        resp = await client.get(f"/admin/coupons/{coupon['_id']}/usage", headers=admin["headers"])
        assert resp.json()["data"]["meta"]["total"] == 0

    async def test_max_discount_on_flat_coupon_rejected(self, client, admin):
        resp = await client.post("/admin/coupons", headers=admin["headers"], json={
            "code": "FLATREJECT", "discount_type": "flat", "discount_value": 50, "max_discount": 100,
        })
        assert resp.status_code == 400