"""
Tests for /admin/dashboard/* — distinct from /admin/analytics/* (dashboard is the
at-a-glance operational view; analytics is the deeper reporting module).
"""
import pytest
from datetime import datetime


async def _place_order(client, customer, product, address):
    await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
    resp = await client.post("/orders", headers=customer["headers"], json={"address_id": address, "payment_method": "cod"})
    return resp.json()["data"]["id"]


class TestDashboardStats:
    async def test_stats_reflects_todays_order(self, client, admin, customer, product, address):
        await _place_order(client, customer, product, address)
        resp = await client.get("/admin/dashboard/stats", headers=admin["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["orders_today"] >= 1
        assert resp.json()["data"]["revenue_today"] >= product["price"]

    async def test_avg_order_value_computed(self, client, admin, customer, product, address):
        await _place_order(client, customer, product, address)
        resp = await client.get("/admin/dashboard/stats", headers=admin["headers"])
        assert resp.json()["data"]["avg_order_value_today"] > 0


class TestDailyMonthlySales:
    async def test_daily_sales_current_month_shape(self, client, admin, customer, product, address):
        await _place_order(client, customer, product, address)
        resp = await client.get("/admin/dashboard/sales/daily", headers=admin["headers"])
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["month"] == datetime.utcnow().strftime("%Y-%m")
        today_entry = next(d for d in data["data"] if d["day"] == datetime.utcnow().day)
        assert today_entry["order_count"] >= 1

    async def test_monthly_sales_current_year_shape(self, client, admin, customer, product, address):
        await _place_order(client, customer, product, address)
        resp = await client.get("/admin/dashboard/sales/monthly", headers=admin["headers"])
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["year"] == datetime.utcnow().year
        assert len(data["data"]) == 12
        this_month = next(m for m in data["data"] if m["month"] == datetime.utcnow().month)
        assert this_month["order_count"] >= 1

    async def test_daily_sales_zero_fills_days_with_no_orders(self, client, admin):
        resp = await client.get("/admin/dashboard/sales/daily", headers=admin["headers"])
        assert all(d["revenue"] >= 0 for d in resp.json()["data"]["data"])


class TestHourlyHeatmap:
    async def test_hourly_heatmap_shape(self, client, admin, customer, product, address):
        await _place_order(client, customer, product, address)
        resp = await client.get("/admin/dashboard/sales/hourly", headers=admin["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["period"] == "last_30_days"
        for point in resp.json()["data"]["data"]:
            assert 1 <= point["day_of_week"] <= 7
            assert 0 <= point["hour"] <= 23


class TestTopProducts:
    async def test_top_products_reflects_total_sold(self, client, admin, customer, product, address):
        await _place_order(client, customer, product, address)
        resp = await client.get("/admin/dashboard/top-products", headers=admin["headers"])
        assert resp.status_code == 200
        matching = [p for p in resp.json()["data"] if p["id"] == str(product["_id"])]
        assert matching and matching[0]["total_sold"] == 1

    async def test_top_products_respects_limit(self, client, admin):
        resp = await client.get("/admin/dashboard/top-products?limit=3", headers=admin["headers"])
        assert resp.status_code == 200
        assert len(resp.json()["data"]) <= 3


class TestLowStock:
    async def test_product_below_threshold_appears(self, client, admin, product, db):
        await db.products.update_one({"_id": product["_id"]}, {"$set": {"stock": 2, "low_stock_threshold": 5}})
        resp = await client.get("/admin/dashboard/low-stock", headers=admin["headers"])
        assert resp.status_code == 200
        assert any(p["id"] == str(product["_id"]) for p in resp.json()["data"])

    async def test_product_above_threshold_excluded(self, client, admin, product, db):
        await db.products.update_one({"_id": product["_id"]}, {"$set": {"stock": 100, "low_stock_threshold": 5}})
        resp = await client.get("/admin/dashboard/low-stock", headers=admin["headers"])
        assert not any(p["id"] == str(product["_id"]) for p in resp.json()["data"])

    async def test_variant_level_low_stock_detected(self, client, admin, category, db):
        now = datetime.utcnow()
        result = await db.products.insert_one({
            "name": "Variant Cake", "slug": "variant-cake", "description": "x",
            "category": category["slug"], "price": 500, "images": [], "tags": [],
            "variants": [{"name": "500g", "price": 400, "stock": 1}, {"name": "1kg", "price": 700, "stock": 50}],
            "is_eggless": False, "stock": 0, "low_stock_threshold": 5,
            "is_available": True, "is_featured": False, "total_sold": 0, "avg_rating": 0, "review_count": 0,
            "created_at": now, "updated_at": now,
        })
        resp = await client.get("/admin/dashboard/low-stock", headers=admin["headers"])
        low_stock_items = resp.json()["data"]
        matching = [i for i in low_stock_items if i["id"] == str(result.inserted_id) and i["variant_name"] == "500g"]
        assert matching
        assert not any(i["id"] == str(result.inserted_id) and i["variant_name"] == "1kg" for i in low_stock_items)


class TestPendingOrders:
    async def test_pending_order_appears_in_queue(self, client, admin, customer, product, address):
        order_id = await _place_order(client, customer, product, address)
        resp = await client.get("/admin/dashboard/pending-orders", headers=admin["headers"])
        assert resp.status_code == 200
        assert any(o["id"] == order_id for o in resp.json()["data"]["items"])

    async def test_confirmed_order_no_longer_pending(self, client, admin, customer, product, address):
        order_id = await _place_order(client, customer, product, address)
        await client.put(f"/admin/orders/{order_id}/status", headers=admin["headers"], json={"status": "confirmed"})
        resp = await client.get("/admin/dashboard/pending-orders", headers=admin["headers"])
        assert not any(o["id"] == order_id for o in resp.json()["data"]["items"])

    async def test_pending_orders_oldest_first(self, client, admin, customer, product, address):
        first = await _place_order(client, customer, product, address)
        second = await _place_order(client, customer, product, address)
        resp = await client.get("/admin/dashboard/pending-orders", headers=admin["headers"])
        ids = [o["id"] for o in resp.json()["data"]["items"]]
        assert ids.index(first) < ids.index(second)


class TestDashboardAuthGating:
    async def test_customer_cannot_access_any_dashboard_route(self, client, customer):
        for path in ["/admin/dashboard/sales/daily", "/admin/dashboard/top-products",
                      "/admin/dashboard/low-stock", "/admin/dashboard/pending-orders"]:
            resp = await client.get(path, headers=customer["headers"])
            assert resp.status_code == 403, f"{path} should reject a customer"