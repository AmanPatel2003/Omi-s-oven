"""
Tests for /orders/*, /payments/*.

Highest-stakes module in the app — covers:
- ownership enforcement (a customer must never see/cancel another's order — IDOR)
- stock deduction on order placement, restock on cancellation
- Razorpay webhook HMAC signature verification (must reject forged webhooks)
- refund authorization (admin-only)
"""
import hmac
import hashlib
import pytest


async def _place_order(client, customer, product, address_id):
    await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
    return await client.post("/orders", headers=customer["headers"],
                              json={"address_id": address_id, "payment_method": "cod"})


class TestPlaceOrder:
    async def test_place_order_success(self, client, customer, product, address):
        resp = await _place_order(client, customer, product, address)
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "pending"

    async def test_place_order_empty_cart_rejected(self, client, customer, address):
        resp = await client.post("/orders", headers=customer["headers"],
                                  json={"address_id": address, "payment_method": "cod"})
        assert resp.status_code == 400

    async def test_place_order_invalid_address_rejected(self, client, customer, product):
        await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
        resp = await client.post("/orders", headers=customer["headers"],
                                  json={"address_id": "nonexistent", "payment_method": "cod"})
        assert resp.status_code == 404

    async def test_place_order_deducts_stock(self, client, customer, product, address, db):
        original_stock = product["stock"]
        await _place_order(client, customer, product, address)
        updated = await db.products.find_one({"_id": product["_id"]})
        assert updated["stock"] == original_stock - 1
        assert updated["total_sold"] == 1

    async def test_place_order_out_of_stock_rejected(self, client, customer, product, address, db):
        await db.products.update_one({"_id": product["_id"]}, {"$set": {"stock": 0}})
        await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
        resp = await client.post("/orders", headers=customer["headers"],
                                  json={"address_id": address, "payment_method": "cod"})
        assert resp.status_code == 400

    async def test_place_order_clears_cart(self, client, customer, product, address):
        await _place_order(client, customer, product, address)
        cart = await client.get("/cart", headers=customer["headers"])
        assert len(cart.json()["data"]["items"]) == 0

    async def test_order_total_matches_cart_summary_not_client_input(self, client, customer, product, address):
        """Order total is server-computed — client cannot pass a total in the request body at all."""
        resp = await _place_order(client, customer, product, address)
        assert resp.json()["data"]["total"] == product["price"]  # no tax/discount in fixture, base case


class TestOrderOwnership:
    async def test_customer_cannot_view_another_customers_order(self, client, customer, second_customer, product, address):
        order_resp = await _place_order(client, customer, product, address)
        order_id = order_resp.json()["data"]["id"]
        resp = await client.get(f"/orders/{order_id}", headers=second_customer["headers"])
        assert resp.status_code == 404   # not 403 — must not reveal existence either

    async def test_customer_cannot_cancel_another_customers_order(self, client, customer, second_customer, product, address):
        order_resp = await _place_order(client, customer, product, address)
        order_id = order_resp.json()["data"]["id"]
        resp = await client.post(f"/orders/{order_id}/cancel", headers=second_customer["headers"])
        assert resp.status_code == 404

    async def test_customer_cannot_track_another_customers_order(self, client, customer, second_customer, product, address):
        order_resp = await _place_order(client, customer, product, address)
        order_id = order_resp.json()["data"]["id"]
        resp = await client.get(f"/delivery/track/{order_id}", headers=second_customer["headers"])
        assert resp.status_code == 404


class TestCancelOrder:
    async def test_cancel_pending_order_restocks(self, client, customer, product, address, db):
        original_stock = product["stock"]
        order_resp = await _place_order(client, customer, product, address)
        order_id = order_resp.json()["data"]["id"]

        resp = await client.post(f"/orders/{order_id}/cancel", headers=customer["headers"])
        assert resp.status_code == 200

        updated = await db.products.find_one({"_id": product["_id"]})
        assert updated["stock"] == original_stock

    async def test_cannot_cancel_already_delivered_order(self, client, customer, product, address, db):
        from bson import ObjectId
        order_resp = await _place_order(client, customer, product, address)
        order_id = order_resp.json()["data"]["id"]
        await db.orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": "delivered"}})

        resp = await client.post(f"/orders/{order_id}/cancel", headers=customer["headers"])
        assert resp.status_code == 400


class TestReorder:
    async def test_reorder_adds_items_to_cart(self, client, customer, product, address):
        order_resp = await _place_order(client, customer, product, address)
        order_id = order_resp.json()["data"]["id"]

        resp = await client.post(f"/orders/{order_id}/reorder", headers=customer["headers"])
        assert resp.status_code == 200
        assert product["name"] in resp.json()["data"]["added"]

        cart = await client.get("/cart", headers=customer["headers"])
        assert len(cart.json()["data"]["items"]) == 1

    async def test_reorder_skips_deactivated_product(self, client, customer, product, address, db):
        order_resp = await _place_order(client, customer, product, address)
        order_id = order_resp.json()["data"]["id"]
        await db.products.update_one({"_id": product["_id"]}, {"$set": {"is_available": False}})

        resp = await client.post(f"/orders/{order_id}/reorder", headers=customer["headers"])
        assert product["name"] in resp.json()["data"]["skipped"]


class TestActiveOrdersRouteOrdering:
    async def test_active_route_not_swallowed_by_id_route(self, client, customer):
        """Regression: /orders/active must resolve before /orders/{order_id}."""
        resp = await client.get("/orders/active", headers=customer["headers"])
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)


class TestPaymentCreate:
    async def test_create_payment_for_own_order(self, client, customer, product, address):
        order_resp = await _place_order(client, customer, product, address)
        order_id = order_resp.json()["data"]["id"]
        resp = await client.post("/payments/create", headers=customer["headers"], json={"order_id": order_id})
        assert resp.status_code == 200
        assert "razorpay_order_id" in resp.json()["data"]

    async def test_create_payment_amount_is_paise_not_rupees(self, client, customer, product, address):
        order_resp = await _place_order(client, customer, product, address)
        order_id = order_resp.json()["data"]["id"]
        resp = await client.post("/payments/create", headers=customer["headers"], json={"order_id": order_id})
        assert resp.json()["data"]["amount"] == int(round(product["price"] * 100))

    async def test_cannot_create_payment_for_already_paid_order(self, client, customer, product, address, db):
        from bson import ObjectId
        order_resp = await _place_order(client, customer, product, address)
        order_id = order_resp.json()["data"]["id"]
        await db.orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"payment_status": "paid"}})
        resp = await client.post("/payments/create", headers=customer["headers"], json={"order_id": order_id})
        assert resp.status_code == 400


class TestPaymentVerify:
    async def test_verify_with_correct_signature_succeeds(self, client, customer, product, address, db):
        from app.core.config import settings
        order_resp = await _place_order(client, customer, product, address)
        order_id = order_resp.json()["data"]["id"]
        await client.post("/payments/create", headers=customer["headers"], json={"order_id": order_id})

        payment = await db.payments.find_one({"order_id": order_id})
        razorpay_order_id = payment["razorpay_order_id"]
        razorpay_payment_id = "pay_test123"
        body = f"{razorpay_order_id}|{razorpay_payment_id}"
        signature = hmac.new(settings.RAZORPAY_KEY_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()

        resp = await client.post("/payments/verify", headers=customer["headers"], json={
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": signature,
        })
        assert resp.status_code == 200

    async def test_verify_with_tampered_signature_rejected(self, client, customer, product, address, db):
        order_resp = await _place_order(client, customer, product, address)
        order_id = order_resp.json()["data"]["id"]
        await client.post("/payments/create", headers=customer["headers"], json={"order_id": order_id})
        payment = await db.payments.find_one({"order_id": order_id})

        resp = await client.post("/payments/verify", headers=customer["headers"], json={
            "razorpay_order_id": payment["razorpay_order_id"],
            "razorpay_payment_id": "pay_test123",
            "razorpay_signature": "0" * 64,   # forged
        })
        assert resp.status_code == 400


class TestPaymentWebhook:
    async def test_webhook_with_valid_signature_marks_order_paid(self, client, customer, product, address, db):
        from app.core.config import settings
        import json

        order_resp = await _place_order(client, customer, product, address)
        order_id = order_resp.json()["data"]["id"]
        await client.post("/payments/create", headers=customer["headers"], json={"order_id": order_id})
        payment = await db.payments.find_one({"order_id": order_id})

        payload = {
            "event": "payment.captured",
            "payload": {"payment": {"entity": {
                "id": "pay_webhook123", "order_id": payment["razorpay_order_id"], "method": "upi",
            }}},
        }
        raw_body = json.dumps(payload).encode()
        signature = hmac.new(settings.RAZORPAY_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()

        resp = await client.post("/payments/webhook", content=raw_body,
                                  headers={"X-Razorpay-Signature": signature, "Content-Type": "application/json"})
        assert resp.status_code == 200

        from bson import ObjectId
        order = await db.orders.find_one({"_id": ObjectId(order_id)})
        assert order["payment_status"] == "paid"
        assert order["status"] == "confirmed"

    async def test_webhook_with_forged_signature_rejected(self, client):
        import json
        payload = {"event": "payment.captured", "payload": {"payment": {"entity": {"id": "x", "order_id": "y"}}}}
        raw_body = json.dumps(payload).encode()
        resp = await client.post("/payments/webhook", content=raw_body,
                                  headers={"X-Razorpay-Signature": "forged" * 10, "Content-Type": "application/json"})
        assert resp.status_code == 401

    async def test_webhook_is_idempotent_on_duplicate_delivery(self, client, customer, product, address, db):
        """Razorpay may send the same webhook twice — must not double-process."""
        from app.core.config import settings
        import json

        order_resp = await _place_order(client, customer, product, address)
        order_id = order_resp.json()["data"]["id"]
        await client.post("/payments/create", headers=customer["headers"], json={"order_id": order_id})
        payment = await db.payments.find_one({"order_id": order_id})

        payload = {
            "event": "payment.captured",
            "payload": {"payment": {"entity": {"id": "pay_dup1", "order_id": payment["razorpay_order_id"], "method": "upi"}}},
        }
        raw_body = json.dumps(payload).encode()
        signature = hmac.new(settings.RAZORPAY_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
        headers = {"X-Razorpay-Signature": signature, "Content-Type": "application/json"}

        first = await client.post("/payments/webhook", content=raw_body, headers=headers)
        second = await client.post("/payments/webhook", content=raw_body, headers=headers)
        assert first.status_code == 200
        assert second.json().get("duplicate") is True


class TestRefund:
    async def test_refund_requires_admin_role(self, client, customer, product, address):
        order_resp = await _place_order(client, customer, product, address)
        order_id = order_resp.json()["data"]["id"]
        resp = await client.post(f"/payments/{order_id}/refund", headers=customer["headers"], json={})
        assert resp.status_code == 403

    async def test_refund_by_admin_on_captured_payment(self, client, customer, admin, product, address, db):
        from bson import ObjectId
        order_resp = await _place_order(client, customer, product, address)
        order_id = order_resp.json()["data"]["id"]
        await client.post("/payments/create", headers=customer["headers"], json={"order_id": order_id})
        payment = await db.payments.find_one({"order_id": order_id})
        await db.payments.update_one({"_id": payment["_id"]}, {"$set": {
            "status": "captured", "razorpay_payment_id": "pay_test123",
        }})

        resp = await client.post(f"/payments/{order_id}/refund", headers=admin["headers"], json={"reason": "Customer request"})
        assert resp.status_code == 200
        assert resp.json()["data"]["refund_status"] == "processed"