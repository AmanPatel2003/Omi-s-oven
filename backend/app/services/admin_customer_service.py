from datetime import datetime
from bson import ObjectId

from app.core.exceptions import NotFoundException, BadRequestException
from app.services import reward_service


def _to_object_id(id_str: str, label: str = "id"):
    try:
        return ObjectId(id_str)
    except Exception:
        raise BadRequestException(f"Invalid {label}")


REVENUE_STATUS_FILTER = {"$ne": "cancelled"}


# ── LIST ALL CUSTOMERS (with order count + spend) ────────────────────
async def list_customers(db, search: str | None = None, page: int = 1, limit: int = 20) -> dict:
    query = {"role": "customer"}
    if search:
        search = search.strip()
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}},
        ]

    page = max(page, 1)
    limit = min(max(limit, 1), 100)
    skip = (page - 1) * limit

    total = await db.users.count_documents(query)
    cursor = db.users.find(query).sort([("created_at", -1)]).skip(skip).limit(limit)
    customers = await cursor.to_list(length=limit)

    items = []
    for c in customers:
        cid = str(c["_id"])

        order_pipeline = [
            {"$match": {"user_id": cid, "status": REVENUE_STATUS_FILTER}},
            {"$group": {"_id": None, "count": {"$sum": 1}, "total": {"$sum": "$total"}}},
        ]
        order_result = await db.orders.aggregate(order_pipeline).to_list(length=1)
        order_count = order_result[0]["count"] if order_result else 0
        total_spend = round(order_result[0]["total"], 2) if order_result else 0.0

        reward = await db.rewards.find_one({"user_id": cid})
        reward_points = reward["total_points"] if reward else 0

        items.append({
            "id": cid,
            "name": c["name"],
            "email": c["email"],
            "phone": c["phone"],
            "is_active": c.get("is_active", True),
            "order_count": order_count,
            "total_spend": total_spend,
            "reward_points": reward_points,
            "joined_at": c["created_at"],
        })

    return {
        "items": items,
        "meta": {
            "page": page, "limit": limit, "total": total,
            "total_pages": (total + limit - 1) // limit if total else 0,
        },
    }


# ── SINGLE CUSTOMER DETAIL ─────────────────────────────────────────────
async def get_customer(db, customer_id: str) -> dict:
    oid = _to_object_id(customer_id, "customer id")
    customer = await db.users.find_one({"_id": oid, "role": "customer"})
    if not customer:
        raise NotFoundException("Customer not found")

    order_pipeline = [
        {"$match": {"user_id": customer_id, "status": REVENUE_STATUS_FILTER}},
        {"$group": {"_id": None, "count": {"$sum": 1}, "total": {"$sum": "$total"}}},
    ]
    order_result = await db.orders.aggregate(order_pipeline).to_list(length=1)
    order_count = order_result[0]["count"] if order_result else 0
    total_spend = round(order_result[0]["total"], 2) if order_result else 0.0
    avg_order_value = round(total_spend / order_count, 2) if order_count else 0.0

    reward = await db.rewards.find_one({"user_id": customer_id})
    reward_points = reward["total_points"] if reward else 0
    lifetime_points = reward["lifetime_points"] if reward else 0

    from app.core.config import TIERS
    current_tier = TIERS[0]["name"]
    for tier in TIERS:
        if lifetime_points >= tier["min_lifetime_points"]:
            current_tier = tier["name"]

    addresses = [
        {"full_name": a["full_name"], "city": a["city"], "is_default": a.get("is_default", False)}
        for a in customer.get("addresses", [])
    ]

    recent_cursor = db.orders.find({"user_id": customer_id}).sort([("created_at", -1)]).limit(10)
    recent_orders = []
    async for o in recent_cursor:
        recent_orders.append({
            "id": str(o["_id"]),
            "order_number": o["order_number"],
            "total": o["total"],
            "status": o["status"],
            "payment_status": o["payment_status"],
            "created_at": o["created_at"],
        })

    return {
        "id": customer_id,
        "name": customer["name"],
        "email": customer["email"],
        "phone": customer["phone"],
        "is_active": customer.get("is_active", True),
        "joined_at": customer["created_at"],
        "order_count": order_count,
        "total_spend": total_spend,
        "avg_order_value": avg_order_value,
        "reward_points": reward_points,
        "lifetime_points": lifetime_points,
        "loyalty_tier": current_tier,
        "addresses": addresses,
        "recent_orders": recent_orders,
    }


# ── BLOCK / UNBLOCK ────────────────────────────────────────────────────
async def toggle_block(db, customer_id: str, reason: str | None) -> dict:
    oid = _to_object_id(customer_id, "customer id")
    customer = await db.users.find_one({"_id": oid, "role": "customer"})
    if not customer:
        raise NotFoundException("Customer not found")

    new_status = not customer.get("is_active", True)
    await db.users.update_one(
        {"_id": oid},
        {"$set": {"is_active": new_status, "updated_at": datetime.utcnow()}},
    )

    action = "unblocked" if new_status else "blocked"
    return {
        "id": customer_id,
        "is_active": new_status,
        "message": f"Customer {action}" + (f" — reason: {reason}" if reason and not new_status else ""),
    }


# ── MANUAL REWARD ADJUSTMENT (routed through the shared reward ledger) ──
async def adjust_reward(db, customer_id: str, admin_id: str, points: int, reason: str) -> dict:
    oid = _to_object_id(customer_id, "customer id")
    customer = await db.users.find_one({"_id": oid, "role": "customer"})
    if not customer:
        raise NotFoundException("Customer not found")

    reward = await db.rewards.find_one({"user_id": customer_id})
    current_balance = reward["total_points"] if reward else 0

    if points < 0 and current_balance + points < 0:
        raise BadRequestException(
            f"Cannot deduct {abs(points)} points — customer only has {current_balance}"
        )

    now = datetime.utcnow()
    txn = {
        "type": "adjustment",
        "points": points,
        "order_id": None,
        "description": f"Admin adjustment: {reason}",
        "created_at": now,
    }

    inc_fields = {"total_points": points}
    if points > 0:
        inc_fields["lifetime_points"] = points   # only positive adjustments count toward tier progress

    await db.rewards.update_one(
        {"user_id": customer_id},
        {"$inc": inc_fields, "$push": {"transactions": txn}, "$set": {"updated_at": now}},
        upsert=True,
    )

    updated = await db.rewards.find_one({"user_id": customer_id})

    return {
        "customer_id": customer_id,
        "points_adjusted": points,
        "new_balance": updated["total_points"],
        "reason": reason,
    }