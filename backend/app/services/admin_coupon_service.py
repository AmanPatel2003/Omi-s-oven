from datetime import datetime
from bson import ObjectId

from app.core.exceptions import NotFoundException, BadRequestException, ConflictException


def _to_object_id(id_str: str, label: str = "id"):
    try:
        return ObjectId(id_str)
    except Exception:
        raise BadRequestException(f"Invalid {label}")


async def _out_with_stats(db, doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))

    now = datetime.utcnow()
    doc["is_expired"] = bool(doc.get("expires_at") and doc["expires_at"] < now)

    if doc.get("usage_limit") is not None:
        doc["usage_remaining"] = max(doc["usage_limit"] - doc.get("used_count", 0), 0)
    else:
        doc["usage_remaining"] = None

    # sum actual discount given across usage records — more accurate than
    # estimating from used_count * discount_value, since flat/percentage/max_discount
    # can all produce different real discounts per order
    pipeline = [
        {"$match": {"coupon_code": doc["code"]}},
        {"$group": {"_id": None, "total": {"$sum": "$discount_amount"}}},
    ]
    result = await db.coupon_usage.aggregate(pipeline).to_list(length=1)
    doc["total_discount_given"] = round(result[0]["total"], 2) if result else 0.0

    return doc


# ── LIST ALL (with usage stats) ────────────────────────────────────
async def list_coupons(db) -> list:
    cursor = db.coupons.find({}).sort([("created_at", -1)])
    items = []
    async for doc in cursor:
        items.append(await _out_with_stats(db, doc))
    return items


# ── CREATE ──────────────────────────────────────────────────────────
async def create_coupon(db, data: dict) -> dict:
    if await db.coupons.find_one({"code": data["code"]}):
        raise ConflictException("A coupon with this code already exists")

    if data.get("max_discount") is not None and data["discount_type"] == "flat":
        raise BadRequestException("max_discount only applies to percentage-type coupons")

    now = datetime.utcnow()
    doc = {**data, "used_count": 0, "is_active": True, "created_at": now}
    result = await db.coupons.insert_one(doc)
    doc["_id"] = result.inserted_id
    return await _out_with_stats(db, doc)


# ── UPDATE ──────────────────────────────────────────────────────────
async def update_coupon(db, coupon_id: str, data: dict) -> dict:
    oid = _to_object_id(coupon_id, "coupon id")
    coupon = await db.coupons.find_one({"_id": oid})
    if not coupon:
        raise NotFoundException("Coupon not found")

    update_data = {k: v for k, v in data.items() if v is not None}
    if not update_data:
        raise BadRequestException("No fields to update")

    # if lowering usage_limit below already-used count, block it — confusing state otherwise
    new_limit = update_data.get("usage_limit")
    if new_limit is not None and new_limit < coupon.get("used_count", 0):
        raise BadRequestException(
            f"Cannot set usage_limit below current used_count ({coupon.get('used_count', 0)})"
        )

    await db.coupons.update_one({"_id": oid}, {"$set": update_data})
    updated = await db.coupons.find_one({"_id": oid})
    return await _out_with_stats(db, updated)


# ── DEACTIVATE ────────────────────────────────────────────────────────
async def deactivate_coupon(db, coupon_id: str) -> dict:
    oid = _to_object_id(coupon_id, "coupon id")
    coupon = await db.coupons.find_one({"_id": oid})
    if not coupon:
        raise NotFoundException("Coupon not found")

    await db.coupons.update_one({"_id": oid}, {"$set": {"is_active": False}})
    updated = await db.coupons.find_one({"_id": oid})
    return await _out_with_stats(db, updated)


# ── USAGE HISTORY ─────────────────────────────────────────────────────
async def get_usage(db, coupon_id: str, page: int = 1, limit: int = 20) -> dict:
    oid = _to_object_id(coupon_id, "coupon id")
    coupon = await db.coupons.find_one({"_id": oid})
    if not coupon:
        raise NotFoundException("Coupon not found")

    page = max(page, 1)
    limit = min(max(limit, 1), 100)
    skip = (page - 1) * limit

    query = {"coupon_code": coupon["code"]}
    total = await db.coupon_usage.count_documents(query)
    cursor = db.coupon_usage.find(query).sort([("used_at", -1)]).skip(skip).limit(limit)

    items = []
    async for u in cursor:
        user = await db.users.find_one({"_id": ObjectId(u["user_id"])})
        order = await db.orders.find_one({"_id": ObjectId(u["order_id"])})
        items.append({
            "user_id": u["user_id"],
            "user_name": user["name"] if user else "Unknown",
            "user_email": user["email"] if user else "",
            "order_id": u["order_id"],
            "order_number": order["order_number"] if order else "N/A",
            "discount_amount": u["discount_amount"],
            "order_total": u["order_total"],
            "used_at": u["used_at"],
        })

    return {
        "coupon_code": coupon["code"],
        "items": items,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total else 0,
        },
    }