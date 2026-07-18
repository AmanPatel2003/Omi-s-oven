"""
Tests for /delivery/track/:order_id (customer) and /staff/orders/*, /staff/location (rider).

The most important test in this file is test_unassigned_rider_cannot_push_location —
it's a direct regression test for the auto-claim security hole we removed from
delivery_service.update_location.
"""
import pytest
from bson import ObjectId


async def _place_order(client, customer, product, address):
    await client.post("/cart/add", headers=customer["headers"], json={"product_id": str(product["_id"]), "qty": 1})
    resp = await client.post("/orders", headers=customer["headers"],
                              json={"address_id": address, "payment_method": "cod"})
    return resp.json()["data"]["id"]


async def _advance_to_out_for_delivery(client, admin, delivery_staff, order_id):
    await client.put(f"/admin/orders/{order_id}/status", headers=admin["headers"], json={"status": "confirmed"})
    await client.put(f"/admin/orders/{order_id}/status", headers=admin["headers"], json={"status": "preparing"})
    await client.post(f"/admin/orders/{order_id}/assign-delivery", headers=admin["headers"],
                       json={"rider_id": delivery_staff["id"]})
    await client.put(f"/admin/orders/{order_id}/status", headers=admin["headers"], json={"status": "out_for_delivery"})


class TestCustomerTracking:
    async def test_track_before_dispatch_returns_null_location_not_error(self, client, customer, product, address, admin):
        order_id = await _place_order(client, customer, product, address)
        await client.put(f"/admin/orders/{order_id}/status", headers=admin["headers"], json={"status": "confirmed"})

        resp = await client.get(f"/delivery/track/{order_id}", headers=customer["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["current_location"] is None

    async def test_track_cross_user_404(self, client, customer, second_customer, product, address):
        order_id = await _place_order(client, customer, product, address)
        resp = await client.get(f"/delivery/track/{order_id}", headers=second_customer["headers"])
        assert resp.status_code == 404

    async def test_track_after_location_push_shows_coordinates(self, client, customer, admin, delivery_staff, product, address):
        order_id = await _place_order(client, customer, product, address)
        await _advance_to_out_for_delivery(client, admin, delivery_staff, order_id)

        await client.post("/staff/location", headers=delivery_staff["headers"],
                           json={"order_id": order_id, "lat": 23.1815, "lng": 79.9864})

        resp = await client.get(f"/delivery/track/{order_id}", headers=customer["headers"])
        assert resp.json()["data"]["current_location"]["lat"] == 23.1815


class TestStaffPickup:
    async def test_pickup_by_unassigned_rider_rejected(self, client, customer, admin, delivery_staff, product, address, db):
        order_id = await _place_order(client, customer, product, address)
        await client.put(f"/admin/orders/{order_id}/status", headers=admin["headers"], json={"status": "confirmed"})

        # a second rider who was never assigned tries to claim it
        second_rider = {"headers": delivery_staff["headers"]}  # reuse same fixture user for simplicity of this check
        # create a genuinely different, unassigned rider instead:
        from app.core.security import hash_password, create_access_token
        now = __import__("datetime").datetime.utcnow()
        result = await db.users.insert_one({
            "name": "Unassigned Rider", "email": "unassigned@test.com", "phone": "9000000001",
            "password_hash": hash_password("x"), "role": "delivery_staff", "is_active": True,
            "created_at": now, "updated_at": now,
        })
        rider_token = create_access_token({"sub": str(result.inserted_id), "role": "delivery_staff"})
        rider_headers = {"Authorization": f"Bearer {rider_token}"}

        resp = await client.put(f"/staff/orders/{order_id}/pickup", headers=rider_headers)
        assert resp.status_code == 403

    async def test_pickup_while_pending_rejected(self, client, customer, admin, delivery_staff, product, address):
        order_id = await _place_order(client, customer, product, address)
        # never confirmed — still pending
        resp = await client.put(f"/staff/orders/{order_id}/pickup", headers=delivery_staff["headers"])
        assert resp.status_code == 403  # not assigned yet either, since assign requires confirmed/preparing

    async def test_pickup_success_sets_out_for_delivery(self, client, customer, admin, delivery_staff, product, address):
        order_id = await _place_order(client, customer, product, address)
        await client.put(f"/admin/orders/{order_id}/status", headers=admin["headers"], json={"status": "confirmed"})
        await client.post(f"/admin/orders/{order_id}/assign-delivery", headers=admin["headers"],
                           json={"rider_id": delivery_staff["id"]})

        resp = await client.put(f"/staff/orders/{order_id}/pickup", headers=delivery_staff["headers"])
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "out_for_delivery"


class TestUnassignedRiderCannotAutoClaim:
    """
    Regression test: delivery_service.update_location used to auto-assign
    whichever rider called it first. That's now removed — this test fails
    loudly if the auto-claim behavior is ever reintroduced.
    """
    async def test_unassigned_rider_cannot_push_location(self, client, customer, admin, delivery_staff, product, address, db):
        order_id = await _place_order(client, customer, product, address)
        await client.put(f"/admin/orders/{order_id}/status", headers=admin["headers"], json={"status": "confirmed"})
        await client.put(f"/admin/orders/{order_id}/status", headers=admin["headers"], json={"status": "preparing"})
        await client.post(f"/admin/orders/{order_id}/assign-delivery", headers=admin["headers"],
                           json={"rider_id": delivery_staff["id"]})
        await client.put(f"/admin/orders/{order_id}/status", headers=admin["headers"], json={"status": "out_for_delivery"})

        from app.core.security import hash_password, create_access_token
        now = __import__("datetime").datetime.utcnow()
        result = await db.users.insert_one({
            "name": "Rogue Rider", "email": "rogue@test.com", "phone": "9000000002",
            "password_hash": hash_password("x"), "role": "delivery_staff", "is_active": True,
            "created_at": now, "updated_at": now,
        })
        rogue_token = create_access_token({"sub": str(result.inserted_id), "role": "delivery_staff"})
        rogue_headers = {"Authorization": f"Bearer {rogue_token}"}

        resp = await client.post("/staff/location", headers=rogue_headers,
                                  json={"order_id": order_id, "lat": 23.0, "lng": 79.0})
        assert resp.status_code == 403

        # confirm the delivery doc's rider_id was NOT overwritten by the rogue attempt
        delivery = await db.deliveries.find_one({"order_id": order_id})
        assert delivery["rider_id"] == delivery_staff["id"]


class TestLocationValidation:
    async def test_invalid_latitude_rejected(self, client, customer, admin, delivery_staff, product, address):
        order_id = await _place_order(client, customer, product, address)
        await _advance_to_out_for_delivery(client, admin, delivery_staff, order_id)
        resp = await client.post("/staff/location", headers=delivery_staff["headers"],
                                  json={"order_id": order_id, "lat": 200, "lng": 79.0})
        assert resp.status_code == 422

    async def test_location_push_before_out_for_delivery_rejected(self, client, customer, admin, delivery_staff, product, address):
        order_id = await _place_order(client, customer, product, address)
        await client.put(f"/admin/orders/{order_id}/status", headers=admin["headers"], json={"status": "confirmed"})
        await client.post(f"/admin/orders/{order_id}/assign-delivery", headers=admin["headers"],
                           json={"rider_id": delivery_staff["id"]})
        # still "confirmed", not yet out_for_delivery
        resp = await client.post("/staff/location", headers=delivery_staff["headers"],
                                  json={"order_id": order_id, "lat": 23.0, "lng": 79.0})
        assert resp.status_code == 400


class TestConfirmDeliveryOTP:
    async def test_wrong_otp_rejected(self, client, customer, admin, delivery_staff, product, address):
        order_id = await _place_order(client, customer, product, address)
        await _advance_to_out_for_delivery(client, admin, delivery_staff, order_id)
        resp = await client.put(f"/staff/orders/{order_id}/delivered", headers=delivery_staff["headers"],
                                 json={"otp": "0000"})
        assert resp.status_code == 400

    async def test_correct_otp_marks_delivered(self, client, customer, admin, delivery_staff, product, address, db):
        order_id = await _place_order(client, customer, product, address)
        await _advance_to_out_for_delivery(client, admin, delivery_staff, order_id)

        delivery = await db.deliveries.find_one({"order_id": order_id})
        real_otp = delivery["otp"]

        resp = await client.put(f"/staff/orders/{order_id}/delivered", headers=delivery_staff["headers"],
                                 json={"otp": real_otp})
        assert resp.status_code == 200

        order = await db.orders.find_one({"_id": ObjectId(order_id)})
        assert order["status"] == "delivered"

    async def test_malformed_otp_rejected_by_validation(self, client, customer, admin, delivery_staff, product, address):
        order_id = await _place_order(client, customer, product, address)
        await _advance_to_out_for_delivery(client, admin, delivery_staff, order_id)
        resp = await client.put(f"/staff/orders/{order_id}/delivered", headers=delivery_staff["headers"],
                                 json={"otp": "12"})
        assert resp.status_code == 422


class TestAssignedOrdersList:
    async def test_assigned_orders_only_shows_own_undelivered(self, client, customer, admin, delivery_staff, product, address):
        order_id = await _place_order(client, customer, product, address)
        await client.put(f"/admin/orders/{order_id}/status", headers=admin["headers"], json={"status": "confirmed"})
        await client.post(f"/admin/orders/{order_id}/assign-delivery", headers=admin["headers"],
                           json={"rider_id": delivery_staff["id"]})

        resp = await client.get("/staff/orders/assigned", headers=delivery_staff["headers"])
        assert resp.status_code == 200
        assert any(o["id"] == order_id for o in resp.json()["data"])

    async def test_delivered_orders_excluded_from_assigned_list(self, client, customer, admin, delivery_staff, product, address, db):
        order_id = await _place_order(client, customer, product, address)
        await _advance_to_out_for_delivery(client, admin, delivery_staff, order_id)
        delivery = await db.deliveries.find_one({"order_id": order_id})
        await client.put(f"/staff/orders/{order_id}/delivered", headers=delivery_staff["headers"],
                          json={"otp": delivery["otp"]})

        resp = await client.get("/staff/orders/assigned", headers=delivery_staff["headers"])
        assert not any(o["id"] == order_id for o in resp.json()["data"])