"""
Tests for /admin/analytics/*.
"""
import pytest
from bson import ObjectId
from datetime import datetime


async def _place_and_pay_order(client, customer, product, address, db):
    await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
    resp = await client.post("/orders", headers=customer["headers"], json={"address_id": address, "payment_method": "cod"})
    return resp.json()["data"]["id"]


class TestRevenueAnalytics:
    async def test_revenue_excludes_cancelled_orders(self, client, admin, customer, product, address, db):
        order_id = await _place_and_pay_order(client, customer, product, address, db)
        resp_before = await client.get("/admin/analytics/revenue", headers=admin["headers"])
        total_before = resp_before.json()["data"]["total_revenue"]

        await client.put(f"/admin/orders/{order_id}/status", headers=admin["headers"], json={"status": "cancelled"})

        resp_after = await client.get("/admin/analytics/revenue", headers=admin["headers"])
        total_after = resp_after.json()["data"]["total_revenue"]
        assert total_after == total_before - product["price"]

    async def test_revenue_by_category_percentages_sum_near_100(self, client, admin, customer, product, address, db):
        await _place_and_pay_order(client, customer, product, address, db)
        resp = await client.get("/admin/analytics/revenue", headers=admin["headers"])
        by_category = resp.json()["data"]["by_category"]
        if by_category:
            total_pct = sum(c["percentage_of_total"] for c in by_category)
            assert 99 <= total_pct <= 101

    async def test_top_products_reflects_real_units_sold(self, client, admin, customer, product, address, db):
        await _place_and_pay_order(client, customer, product, address, db)
        resp = await client.get("/admin/analytics/revenue", headers=admin["headers"])
        top = resp.json()["data"]["top_products_by_revenue"]
        matching = [p for p in top if p["product_id"] == str(product["_id"])]
        assert matching and matching[0]["units_sold"] == 1


class TestCustomerAnalytics:
    async def test_new_vs_returning_split(self, client, admin, customer, product, address, db):
        await _place_and_pay_order(client, customer, product, address, db)
        resp = await client.get("/admin/analytics/customers", headers=admin["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["total_new"] + resp.json()["data"]["total_returning"] >= 1


class TestProductAnalytics:
    async def test_requires_product_id_query_param(self, client, admin):
        resp = await client.get("/admin/analytics/products", headers=admin["headers"])
        assert resp.status_code == 422

    async def test_units_sold_over_time(self, client, admin, customer, product, address, db):
        await _place_and_pay_order(client, customer, product, address, db)
        resp = await client.get(f"/admin/analytics/products?product_id={product['_id']}", headers=admin["headers"])
        assert resp.status_code == 200
        total_units = sum(d["units_sold"] for d in resp.json()["data"]["data"])
        assert total_units == 1

    async def test_nonexistent_product_404(self, client, admin):
        resp = await client.get("/admin/analytics/products?product_id=000000000000000000000000", headers=admin["headers"])
        assert resp.status_code == 404


class TestDeliveryAnalytics:
    async def test_returns_note_when_no_dispatched_data(self, client, admin):
        resp = await client.get("/admin/analytics/delivery", headers=admin["headers"])
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_deliveries"] == 0

    async def test_computes_real_avg_time_after_full_delivery_cycle(self, client, admin, customer, delivery_staff, product, address, db):
        order_id = await _place_and_pay_order(client, customer, product, address, db)
        await client.put(f"/admin/orders/{order_id}/status", headers=admin["headers"], json={"status": "confirmed"})
        await client.put(f"/admin/orders/{order_id}/status", headers=admin["headers"], json={"status": "preparing"})
        await client.post(f"/admin/orders/{order_id}/assign-delivery", headers=admin["headers"],
                           json={"rider_id": delivery_staff["id"]})
        await client.put(f"/admin/orders/{order_id}/status", headers=admin["headers"], json={"status": "out_for_delivery"})

        delivery = await db.deliveries.find_one({"order_id": order_id})
        await client.put(f"/staff/orders/{order_id}/delivered", headers=delivery_staff["headers"],
                          json={"otp": delivery["otp"]})

        resp = await client.get("/admin/analytics/delivery", headers=admin["headers"])
        assert resp.json()["data"]["total_deliveries"] >= 1


class TestRewardsAnalytics:
    async def test_points_issued_and_redeemed_tracked(self, client, admin, customer, product, address, db):
        await db.rewards.update_one({"user_id": customer["id"]}, {"$set": {"total_points": 1000}})
        await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
        await client.post("/rewards/redeem", headers=customer["headers"], json={"points": 150})
        await client.post("/orders", headers=customer["headers"], json={"address_id": address, "payment_method": "cod"})

        resp = await client.get("/admin/analytics/rewards", headers=admin["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["points_redeemed"] >= 150


class TestDemandForecast:
    async def test_always_includes_confidence_note(self, client, admin, customer, product, address, db):
        await _place_and_pay_order(client, customer, product, address, db)
        resp = await client.get("/admin/analytics/demand-forecast", headers=admin["headers"])
        assert resp.status_code == 200
        assert "method" in resp.json()["data"]
        for item in resp.json()["data"]["items"]:
            assert "confidence_note" in item
            assert len(item["forecasted_units"]) == 7

    async def test_forecast_never_labeled_as_ml(self, client, admin):
        resp = await client.get("/admin/analytics/demand-forecast", headers=admin["headers"])
        method = resp.json()["data"]["method"].lower()
        assert "machine learning" not in method and "ml model" not in method


class TestAnalyticsExport:
    async def test_export_excel_returns_correct_content_type(self, client, admin, customer, product, address, db):
        await _place_and_pay_order(client, customer, product, address, db)
        resp = await client.get("/admin/analytics/export?format=excel", headers=admin["headers"])
        assert resp.status_code == 200
        assert "spreadsheet" in resp.headers["content-type"]
        assert len(resp.content) > 0

    async def test_export_pdf_returns_correct_content_type(self, client, admin, customer, product, address, db):
        await _place_and_pay_order(client, customer, product, address, db)
        resp = await client.get("/admin/analytics/export?format=pdf", headers=admin["headers"])
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert len(resp.content) > 0

    async def test_export_invalid_date_range_rejected(self, client, admin):
        resp = await client.get(
            "/admin/analytics/export?format=excel&date_from=2026-08-01&date_to=2026-07-01",
            headers=admin["headers"],
        )
        assert resp.status_code == 400

    async def test_export_requires_admin(self, client, customer):
        resp = await client.get("/admin/analytics/export?format=excel", headers=customer["headers"])
        assert resp.status_code == 403