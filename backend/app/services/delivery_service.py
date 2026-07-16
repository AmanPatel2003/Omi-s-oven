import random
from datetime import datetime
from bson import ObjectId

from app.core.exceptions import NotFoundException, BadRequestException, ForbiddenException


def _to_object_id(id_str: str, label: str = "id"):
    try:
        return ObjectId(id_str)
    except Exception:
        raise BadRequestException(f"Invalid {label}")


def generate_otp() -> str:
    return "".join(random.choices("0123456789", k=4))


async def _get_or_create_delivery(db, order_id: str) -> dict:
    delivery = await db.deliveries.find_one({"order_id": order_id})
    if not delivery:
        now = datetime.utcnow()
        delivery = {
            "order_id": order_id,
            "rider_id": None,
            "otp": generate_otp(),
            "otp_verified": False,
            "current_location": None,
            "location_history": [],
            "delivered_at": None,
            "created_at": now,
            "updated_at": now,
        }
        result = await db.deliveries.insert_one(delivery)
        delivery["_id"] = result.inserted_id
    return delivery


# ── CUSTOMER: TRACK ────────────────────────────────────────────
async def track_delivery(db, user_id: str, order_id: str) -> dict:
    order = await db.orders.find_one({
        "_id": _to_object_id(order_id, "order id"),
        "user_id": user_id,   # ownership check — cannot track someone else's order
    })
    if not order:
        raise NotFoundException("Order not found")

    delivery = await db.deliveries.find_one({"order_id": order_id})

    current_location = None
    if delivery and delivery.get("current_location"):
        current_location = delivery["current_location"]

    return {
        "order_id": order_id,
        "order_status": order["status"],
        "current_location": current_location,
        "estimated_delivery": order.get("estimated_delivery"),
        "delivered_at": delivery.get("delivered_at") if delivery else None,
    }


# ── RIDER: PUSH GPS LOCATION ────────────────────────────────────
async def update_location(db, rider_id: str, order_id: str, lat: float, lng: float) -> dict:
    order = await db.orders.find_one({"_id": _to_object_id(order_id, "order id")})
    if not order:
        raise NotFoundException("Order not found")

    if order["status"] != "out_for_delivery":
        raise BadRequestException("Location updates are only allowed while order is out for delivery")

    delivery = await _get_or_create_delivery(db, order_id)

    # first rider to touch this delivery gets auto-assigned;
    # after that, only the assigned rider may push updates
    # if delivery.get("rider_id") is None:
    #     await db.deliveries.update_one({"_id": delivery["_id"]}, {"$set": {"rider_id": rider_id}})
    # elif delivery["rider_id"] != rider_id:
    #     raise ForbiddenException("You are not assigned to this delivery")
    
     # only the rider formally assigned via admin/assign-delivery or staff/pickup may push updates
    if delivery.get("rider_id") != rider_id:
        raise ForbiddenException("You are not assigned to this delivery")


    now = datetime.utcnow()
    ping = {"lat": lat, "lng": lng, "timestamp": now}

    await db.deliveries.update_one(
        {"_id": delivery["_id"]},
        {
            "$set": {"current_location": ping, "updated_at": now},
            "$push": {"location_history": {"$each": [ping], "$slice": -200}},  # cap history to last 200 pings
        },
    )
    return {"order_id": order_id, "location": ping}


# ── RIDER: CONFIRM DELIVERY WITH OTP ────────────────────────────
async def confirm_delivery(db, rider_id: str, order_id: str, otp: str) -> dict:
    order = await db.orders.find_one({"_id": _to_object_id(order_id, "order id")})
    if not order:
        raise NotFoundException("Order not found")

    if order["status"] != "out_for_delivery":
        raise BadRequestException("Order is not currently out for delivery")

    delivery = await db.deliveries.find_one({"order_id": order_id})
    if not delivery:
        raise NotFoundException("Delivery record not found")

    if delivery.get("rider_id") and delivery["rider_id"] != rider_id:
        raise ForbiddenException("You are not assigned to this delivery")

    if delivery.get("otp") != otp:
        raise BadRequestException("Incorrect OTP")

    now = datetime.utcnow()
    await db.deliveries.update_one(
        {"_id": delivery["_id"]},
        {"$set": {"otp_verified": True, "delivered_at": now, "updated_at": now}},
    )
    await db.orders.update_one(
        {"_id": order["_id"]},
        {
            "$set": {"status": "delivered", "updated_at": now},
            "$push": {"status_history": {"status": "delivered", "timestamp": now, "note": "Delivered — OTP verified"}},
        },
    )
    return {"order_id": order_id, "status": "delivered", "delivered_at": now}