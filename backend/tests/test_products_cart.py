"""
Tests for /products/*, /categories/*, /cart/*, /coupons/*.

Key regressions covered:
- static route ordering (/products/featured must not be swallowed by /products/{slug})
- cart never trusts client-sent prices — always re-derives from live product data
- coupon eligibility shared logic (validate vs apply must agree)
"""
import pytest


class TestProductRoutes:
    async def test_list_products_basic(self, client, product):
        resp = await client.get("/products")
        assert resp.status_code == 200
        assert resp.json()["data"]["meta"]["total"] >= 1

    async def test_list_products_filter_by_category(self, client, product, category):
        resp = await client.get(f"/products?category={category['slug']}")
        assert resp.status_code == 200
        assert all(p["category"] == category["slug"] for p in resp.json()["data"]["items"])

    async def test_list_products_price_range_filter(self, client, product):
        resp = await client.get("/products?min_price=1000&max_price=2000")
        assert resp.status_code == 200
        assert len(resp.json()["data"]["items"]) == 0   # our fixture product is ₹599

    async def test_featured_route_not_swallowed_by_slug_route(self, client, product, db):
        """Regression: /products/featured must resolve to the featured endpoint,
        not be interpreted as {slug}='featured'."""
        resp = await client.get("/products/featured")
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)

    async def test_bestsellers_route(self, client, product):
        resp = await client.get("/products/bestsellers")
        assert resp.status_code == 200

    async def test_new_arrivals_route(self, client, product):
        resp = await client.get("/products/new-arrivals")
        assert resp.status_code == 200

    async def test_get_product_by_slug(self, client, product):
        resp = await client.get(f"/products/{product['slug']}")
        assert resp.status_code == 200
        assert resp.json()["data"]["slug"] == product["slug"]

    async def test_get_nonexistent_slug_404(self, client):
        resp = await client.get("/products/does-not-exist")
        assert resp.status_code == 404

    async def test_inactive_product_not_returned_by_slug(self, client, product, db):
        from bson import ObjectId
        await db.products.update_one({"_id": product["_id"]}, {"$set": {"is_available": False}})
        resp = await client.get(f"/products/{product['slug']}")
        assert resp.status_code == 404


class TestReviews:
    async def test_submit_review_requires_auth(self, client, product):
        resp = await client.post(f"/products/{product['_id']}/reviews", json={"rating": 5, "comment": "Great!"})
        assert resp.status_code == 401

    async def test_submit_review_success_updates_avg_rating(self, client, customer, product):
        resp = await client.post(f"/products/{product['_id']}/reviews", headers=customer["headers"],
                                  json={"rating": 5, "comment": "Loved it"})
        assert resp.status_code == 200

        detail = await client.get(f"/products/{product['slug']}")
        assert detail.json()["data"]["avg_rating"] == 5.0
        assert detail.json()["data"]["review_count"] == 1

    async def test_duplicate_review_from_same_user_rejected(self, client, customer, product):
        await client.post(f"/products/{product['_id']}/reviews", headers=customer["headers"], json={"rating": 5})
        resp = await client.post(f"/products/{product['_id']}/reviews", headers=customer["headers"], json={"rating": 3})
        assert resp.status_code == 400

    async def test_rating_out_of_range_rejected(self, client, customer, product):
        resp = await client.post(f"/products/{product['_id']}/reviews", headers=customer["headers"], json={"rating": 6})
        assert resp.status_code == 422


class TestCategories:
    async def test_list_categories(self, client, category):
        resp = await client.get("/categories")
        assert resp.status_code == 200

    async def test_get_category_with_products(self, client, category, product):
        resp = await client.get(f"/categories/{category['slug']}")
        assert resp.status_code == 200
        assert resp.json()["data"]["category"]["slug"] == category["slug"]
        assert resp.json()["data"]["products"]["meta"]["total"] >= 1


class TestCart:
    async def test_add_to_cart_success(self, client, customer, product):
        resp = await client.post("/cart/add", headers=customer["headers"],
                                  json={"product_id": str(product["_id"]), "qty": 2})
        assert resp.status_code == 200
        assert resp.json()["data"]["items"][0]["qty"] == 2

    async def test_cart_price_comes_from_product_not_client(self, client, customer, product):
        """Critical security test: even if a client could somehow inject a price,
        the cart must always compute price from the live product document."""
        resp = await client.post("/cart/add", headers=customer["headers"],
                                  json={"product_id": str(product["_id"]), "qty": 1})
        cart_price = resp.json()["data"]["items"][0]["price"]
        assert cart_price == product["price"]

    async def test_add_more_than_available_stock_rejected(self, client, customer, product):
        resp = await client.post("/cart/add", headers=customer["headers"],
                                  json={"product_id": str(product["_id"]), "qty": 999})
        assert resp.status_code == 400

    async def test_update_cart_item_qty_zero_removes_item(self, client, customer, product):
        await client.post("/cart/add", headers=customer["headers"],
                           json={"product_id": str(product["_id"]), "qty": 2})
        resp = await client.put("/cart/update", headers=customer["headers"],
                                 json={"product_id": str(product["_id"]), "qty": 0})
        assert resp.status_code == 200
        assert len(resp.json()["data"]["items"]) == 0

    async def test_remove_from_cart(self, client, customer, product):
        await client.post("/cart/add", headers=customer["headers"],
                           json={"product_id": str(product["_id"]), "qty": 1})
        resp = await client.delete(f"/cart/remove/{product['_id']}", headers=customer["headers"])
        assert resp.status_code == 200
        assert len(resp.json()["data"]["items"]) == 0

    async def test_clear_cart(self, client, customer, product):
        await client.post("/cart/add", headers=customer["headers"],
                           json={"product_id": str(product["_id"]), "qty": 1})
        resp = await client.delete("/cart/clear", headers=customer["headers"])
        assert resp.status_code == 200
        assert len(resp.json()["data"]["items"]) == 0

    async def test_cart_isolated_between_users(self, client, customer, second_customer, product):
        await client.post("/cart/add", headers=customer["headers"],
                           json={"product_id": str(product["_id"]), "qty": 1})
        resp = await client.get("/cart", headers=second_customer["headers"])
        assert len(resp.json()["data"]["items"]) == 0


class TestCoupons:
    async def test_apply_valid_coupon(self, client, customer, product, coupon):
        await client.post("/cart/add", headers=customer["headers"],
                           json={"product_id": str(product["_id"]), "qty": 1})
        resp = await client.post("/cart/apply-coupon", headers=customer["headers"], json={"code": "SAVE20"})
        assert resp.status_code == 200
        assert resp.json()["data"]["applied_coupon"] == "SAVE20"

    async def test_apply_coupon_below_min_order_rejected(self, client, customer, product, coupon, db):
        from bson import ObjectId
        await db.products.update_one({"_id": product["_id"]}, {"$set": {"price": 100}})
        await client.post("/cart/add", headers=customer["headers"],
                           json={"product_id": str(product["_id"]), "qty": 1})
        resp = await client.post("/cart/apply-coupon", headers=customer["headers"], json={"code": "SAVE20"})
        assert resp.status_code == 400

    async def test_apply_expired_coupon_rejected(self, client, customer, product, db):
        from datetime import datetime, timedelta
        await db.coupons.insert_one({
            "code": "EXPIRED10", "discount_type": "flat", "discount_value": 10,
            "min_order_value": 0, "usage_limit": None, "used_count": 0,
            "is_public": True, "is_active": True,
            "expires_at": datetime.utcnow() - timedelta(days=1), "created_at": datetime.utcnow(),
        })
        await client.post("/cart/add", headers=customer["headers"],
                           json={"product_id": str(product["_id"]), "qty": 1})
        resp = await client.post("/cart/apply-coupon", headers=customer["headers"], json={"code": "EXPIRED10"})
        assert resp.status_code == 400

    async def test_validate_and_apply_agree_on_eligibility(self, client, customer, product, coupon):
        """Regression: validate and apply used to duplicate logic and could drift apart."""
        await client.post("/cart/add", headers=customer["headers"],
                           json={"product_id": str(product["_id"]), "qty": 1})
        validate_resp = await client.post("/coupons/validate", headers=customer["headers"], json={"code": "SAVE20"})
        apply_resp = await client.post("/cart/apply-coupon", headers=customer["headers"], json={"code": "SAVE20"})
        assert validate_resp.json()["data"]["valid"] == (apply_resp.status_code == 200)

    async def test_list_active_public_coupons_no_auth_required(self, client, coupon):
        resp = await client.get("/coupons/active")
        assert resp.status_code == 200
        assert any(c["code"] == "SAVE20" for c in resp.json()["data"])

    async def test_private_coupon_not_in_active_list(self, client, db):
        await db.coupons.insert_one({
            "code": "SECRET50", "discount_type": "flat", "discount_value": 50,
            "min_order_value": 0, "usage_limit": None, "used_count": 0,
            "is_public": False, "is_active": True, "expires_at": None, "created_at": __import__("datetime").datetime.utcnow(),
        })
        resp = await client.get("/coupons/active")
        assert not any(c["code"] == "SECRET50" for c in resp.json()["data"])