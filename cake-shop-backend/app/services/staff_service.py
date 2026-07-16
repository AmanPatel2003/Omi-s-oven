from datetime import datetime
from bson import ObjectId

from app.core.exceptions import NotFoundException, BadRequestException, ConflictException, ForbiddenException


def _to_object_id(id_str: str, label: str = "id"):
    try:
        return ObjectId(id_str)
    except Exception:
        raise BadRequestException(f"Invalid {label}")


def _today_str() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def _compute_hours(check_in, check_out) -> float | None:
    if check_in and check_out and check_out > check_in:
        return round((check_out - check_in).total_seconds() / 3600, 2)
    return None


def _derive_status(check_in, check_out, hours) -> str:
    if not check_in:
        return "absent"
    if hours is not None and hours < 4:
        return "half_day"
    return "present"


# ── SELF CLOCK-IN ──────────────────────────────────────────────────
async def clock_in(db, staff_id: str, note: str | None) -> dict:
    date = _today_str()
    existing = await db.attendance.find_one({"staff_id": staff_id, "date": date})
    if existing and existing.get("check_in"):
        raise ConflictException("You have already clocked in today")

    now = datetime.utcnow()
    if existing:
        await db.attendance.update_one(
            {"_id": existing["_id"]},
            {"$set": {"check_in": now, "status": "present", "note": note, "marked_by": staff_id, "updated_at": now}},
        )
    else:
        await db.attendance.insert_one({
            "staff_id": staff_id, "date": date, "status": "present",
            "check_in": now, "check_out": None, "hours_worked": None,
            "note": note, "marked_by": staff_id, "is_corrected": False,
            "created_at": now, "updated_at": now,
        })
    return {"date": date, "check_in": now, "status": "present"}


# ── SELF CLOCK-OUT ─────────────────────────────────────────────────
async def clock_out(db, staff_id: str, note: str | None) -> dict:
    date = _today_str()
    existing = await db.attendance.find_one({"staff_id": staff_id, "date": date})
    if not existing or not existing.get("check_in"):
        raise BadRequestException("You haven't clocked in today")
    if existing.get("check_out"):
        raise ConflictException("You have already clocked out today")

    now = datetime.utcnow()
    hours = _compute_hours(existing["check_in"], now)
    status = _derive_status(existing["check_in"], now, hours)

    await db.attendance.update_one(
        {"_id": existing["_id"]},
        {"$set": {
            "check_out": now, "hours_worked": hours, "status": status,
            "note": note or existing.get("note"), "updated_at": now,
        }},
    )
    return {"date": date, "check_out": now, "hours_worked": hours, "status": status}


# ── MY ATTENDANCE (current month) ────────────────────────────────────
async def get_my_attendance(db, staff_id: str) -> dict:
    now = datetime.utcnow()
    month = now.strftime("%Y-%m")

    cursor = db.attendance.find({"staff_id": staff_id, "date": {"$regex": f"^{month}"}}).sort([("date", 1)])
    records = []
    counts = {"present": 0, "half_day": 0, "leave": 0, "absent": 0}
    async for a in cursor:
        if a["status"] in counts:
            counts[a["status"]] += 1
        records.append({
            "date": a["date"], "status": a["status"],
            "check_in": a.get("check_in"), "check_out": a.get("check_out"),
            "hours_worked": a.get("hours_worked"),
        })

    return {
        "month": month,
        "present_days": counts["present"], "half_days": counts["half_day"],
        "leave_days": counts["leave"], "absent_days": counts["absent"],
        "records": records,
    }


# ── MY SALARY SLIPS ──────────────────────────────────────────────────
async def get_my_salary(db, staff_id: str) -> dict:
    cursor = db.salary_records.find({"staff_id": staff_id}).sort([("month", -1)])
    items = []
    async for s in cursor:
        items.append({
            "month": s["month"], "net_paid": s["net_paid"],
            "payment_date": s["payment_date"], "payment_method": s["payment_method"],
        })
    return {"items": items}


# ── ASSIGNED DELIVERIES ────────────────────────────────────────────────
async def get_assigned_orders(db, rider_id: str) -> list:
    cursor = db.deliveries.find({"rider_id": rider_id, "delivered_at": None})
    order_ids = [d["order_id"] async for d in cursor]
    if not order_ids:
        return []

    oids = [ObjectId(oid) for oid in order_ids]
    cursor = db.orders.find({
        "_id": {"$in": oids},
        "status": {"$in": ["confirmed", "preparing", "out_for_delivery"]},
    }).sort([("created_at", 1)])

    items = []
    async for o in cursor:
        items.append({
            "id": str(o["_id"]), "order_number": o["order_number"], "status": o["status"],
            "customer_name": o["address"]["full_name"], "customer_phone": o["address"]["phone"],
            "address_line1": o["address"]["address_line1"], "city": o["address"]["city"],
            "landmark": o["address"].get("landmark"),
            "total": o["total"], "item_count": sum(it["qty"] for it in o["items"]),
            "estimated_delivery": o.get("estimated_delivery"),
        })
    return items


# ── MARK PICKUP (rider-triggered dispatch — preparing/confirmed → out_for_delivery) ──
async def mark_pickup(db, rider_id: str, order_id: str) -> dict:
    oid = _to_object_id(order_id, "order id")
    order = await db.orders.find_one({"_id": oid})
    if not order:
        raise NotFoundException("Order not found")

    delivery = await db.deliveries.find_one({"order_id": order_id})
    if not delivery or delivery.get("rider_id") != rider_id:
        raise ForbiddenException("You are not assigned to this delivery")

    if order["status"] not in ("confirmed", "preparing"):
        raise BadRequestException(f"Cannot mark pickup — order is currently '{order['status']}'")

    now = datetime.utcnow()
    await db.orders.update_one(
        {"_id": oid},
        {
            "$set": {"status": "out_for_delivery", "updated_at": now},
            "$push": {"status_history": {"status": "out_for_delivery", "timestamp": now, "note": "Picked up by rider"}},
        },
    )
    await db.deliveries.update_one(
        {"order_id": order_id},
        {"$set": {"dispatched_at": now, "updated_at": now}},
    )

    from app.services import notification_service
    await notification_service.create_notification(
        db, order["user_id"], "out_for_delivery",
        "Out for delivery", "Your order has been picked up and is on its way!",
        reference_id=order_id,
    )

    return {"order_id": order_id, "status": "out_for_delivery", "picked_up_at": now}