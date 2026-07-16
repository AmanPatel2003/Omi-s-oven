import csv
import io
from datetime import datetime, timedelta
from typing import Optional
from bson import ObjectId

from app.core.exceptions import NotFoundException, BadRequestException
from app.schemas.admin_order import VALID_TRANSITIONS
from app.services import notification_service


def _to_object_id(id_str: str, label: str = "id"):
    try:
        return ObjectId(id_str)
    except Exception:
        raise BadRequestException(f"Invalid {label}")


def _out(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


STATUS_MESSAGES = {
    "confirmed": ("Order confirmed", "Your order has been confirmed and will be prepared soon."),
    "preparing": ("Order in the kitchen", "We've started preparing your order."),
    "out_for_delivery": ("Out for delivery", "Your order is on its way!"),
    "delivered": ("Order delivered", "Your order has been delivered. Enjoy!"),
    "cancelled": ("Order cancelled", "Your order has been cancelled."),
}


# ── LIST (filter + search) ──────────────────────────────────────────
async def list_orders(
    db,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> dict:
    query: dict = {}

    if status:
        query["status"] = status

    if date_from or date_to:
        date_filter = {}
        if date_from:
            date_filter["$gte"] = date_from
        if date_to:
            date_filter["$lte"] = date_to
        query["created_at"] = date_filter

    if search:
        search = search.strip()
        query["$or"] = [
            {"order_number": {"$regex": search, "$options": "i"}},
            {"address.full_name": {"$regex": search, "$options": "i"}},
            {"address.phone": {"$regex": search, "$options": "i"}},
        ]

    page = max(page, 1)
    limit = min(max(limit, 1), 100)
    skip = (page - 1) * limit

    total = await db.orders.count_documents(query)
    cursor = db.orders.find(query).sort([("created_at", -1)]).skip(skip).limit(limit)

    items = []
    async for o in cursor:
        items.append({
            "id": str(o["_id"]),
            "order_number": o["order_number"],
            "customer_name": o["address"]["full_name"],
            "customer_phone": o["address"]["phone"],
            "total": o["total"],
            "status": o["status"],
            "payment_status": o["payment_status"],
            "payment_method": o["payment_method"],
            "item_count": sum(it["qty"] for it in o["items"]),
            "created_at": o["created_at"],
        })

    return {
        "items": items,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total else 0,
        },
    }


# ── DETAIL ────────────────────────────────────────────────────────────
async def get_order(db, order_id: str) -> dict:
    order = await db.orders.find_one({"_id": _to_object_id(order_id, "order id")})
    if not order:
        raise NotFoundException("Order not found")

    customer = await db.users.find_one({"_id": ObjectId(order["user_id"])})
    order["customer_email"] = customer.get("email") if customer else None

    delivery = await db.deliveries.find_one({"order_id": order_id})
    if delivery and delivery.get("rider_id"):
        order["assigned_rider_id"] = delivery["rider_id"]
        rider = await db.users.find_one({"_id": ObjectId(delivery["rider_id"])})
        order["assigned_rider_name"] = rider.get("name") if rider else None
    else:
        order["assigned_rider_id"] = None
        order["assigned_rider_name"] = None

    return _out(order)


# ── UPDATE STATUS ──────────────────────────────────────────────────────
async def update_status(db, order_id: str, new_status: str, note: Optional[str]) -> dict:
    oid = _to_object_id(order_id, "order id")
    order = await db.orders.find_one({"_id": oid})
    if not order:
        raise NotFoundException("Order not found")

    current_status = order["status"]
    allowed_next = VALID_TRANSITIONS.get(current_status, [])
    if new_status not in allowed_next:
        raise BadRequestException(
            f"Cannot move order from '{current_status}' to '{new_status}'. "
            f"Allowed next states: {', '.join(allowed_next) or 'none — this is a final status'}"
        )

    now = datetime.utcnow()   # ← moved up so it's available below

    if new_status == "out_for_delivery":
        delivery = await db.deliveries.find_one({"order_id": order_id})
        if not delivery or not delivery.get("rider_id"):
            raise BadRequestException("Assign a delivery rider before marking the order out for delivery")

        # ── NEW: record dispatch timestamp for delivery analytics ──
        await db.deliveries.update_one(
            {"order_id": order_id},
            {"$set": {"dispatched_at": now}},
            upsert=True,
        )
    if new_status == "cancelled":
        # restock — same logic as customer-initiated cancel_order in order_service
        for item in order["items"]:
            item_oid = ObjectId(item["product_id"])
            if item.get("variant_name"):
                await db.products.update_one(
                    {"_id": item_oid, "variants.name": item["variant_name"]},
                    {"$inc": {"variants.$.stock": item["qty"], "total_sold": -item["qty"]}},
                )
            else:
                await db.products.update_one(
                    {"_id": item_oid},
                    {"$inc": {"stock": item["qty"], "total_sold": -item["qty"]}},
                )

    now = datetime.utcnow()
    await db.orders.update_one(
        {"_id": oid},
        {
            "$set": {"status": new_status, "updated_at": now},
            "$push": {"status_history": {"status": new_status, "timestamp": now, "note": note}},
        },
    )

    title, message = STATUS_MESSAGES.get(new_status, (f"Order {new_status}", f"Your order status is now {new_status}."))
    await notification_service.create_notification(
        db, order["user_id"], f"order_{new_status}", title, message, reference_id=order_id,
    )

    return await get_order(db, order_id)


# ── ASSIGN DELIVERY RIDER ───────────────────────────────────────────────
async def assign_delivery(db, order_id: str, rider_id: str) -> dict:
    oid = _to_object_id(order_id, "order id")
    order = await db.orders.find_one({"_id": oid})
    if not order:
        raise NotFoundException("Order not found")

    if order["status"] not in ("confirmed", "preparing"):
        raise BadRequestException(
            f"Cannot assign a rider while order is '{order['status']}'. Order must be confirmed or preparing first."
        )

    rider_oid = _to_object_id(rider_id, "rider id")
    rider = await db.users.find_one({"_id": rider_oid})
    if not rider or rider.get("role") != "delivery_staff":
        raise BadRequestException("Selected user is not a valid delivery staff member")
    if not rider.get("is_active", True):
        raise BadRequestException("This delivery staff account is deactivated")

    now = datetime.utcnow()
    await db.deliveries.update_one(
        {"order_id": order_id},
        {
            "$set": {"rider_id": rider_id, "updated_at": now},
            "$setOnInsert": {
                "otp": "".join(__import__("random").choices("0123456789", k=4)),
                "otp_verified": False,
                "current_location": None,
                "location_history": [],
                "delivered_at": None,
                "created_at": now,
            },
        },
        upsert=True,
    )

    await notification_service.create_notification(
        db, order["user_id"], "rider_assigned",
        "Rider assigned", f"{rider['name']} has been assigned to deliver your order.",
        reference_id=order_id,
    )

    return await get_order(db, order_id)


# ── EXPORT CSV ────────────────────────────────────────────────────────
async def export_orders_csv(db, date_from: datetime, date_to: datetime):
    query = {"created_at": {"$gte": date_from, "$lte": date_to}}
    cursor = db.orders.find(query).sort([("created_at", 1)])

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Order Number", "Date", "Customer Name", "Phone", "Items",
        "Subtotal", "Discount", "Tax", "Delivery Fee", "Total",
        "Coupon", "Status", "Payment Method", "Payment Status",
    ])

    async for o in cursor:
        item_summary = "; ".join(f"{it['name']} x{it['qty']}" for it in o["items"])
        writer.writerow([
            o["order_number"],
            o["created_at"].strftime("%Y-%m-%d %H:%M"),
            o["address"]["full_name"],
            o["address"]["phone"],
            item_summary,
            o["subtotal"],
            o["discount"],
            o["tax"],
            o["delivery_fee"],
            o["total"],
            o.get("coupon_code") or "",
            o["status"],
            o["payment_method"],
            o["payment_status"],
        ])

    buffer.seek(0)
    return buffer