import random
import string
from datetime import datetime
from bson import ObjectId

from app.core.exceptions import NotFoundException, BadRequestException


def _to_object_id(id_str: str, label: str = "id"):
    try:
        return ObjectId(id_str)
    except Exception:
        raise BadRequestException(f"Invalid {label}")


def _generate_request_number() -> str:
    date_part = datetime.utcnow().strftime("%Y%m%d")
    rand_part = "".join(random.choices(string.digits, k=4))
    return f"CO-{date_part}-{rand_part}"


def _out(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


# ── SUBMIT ────────────────────────────────────────────────────
async def submit_custom_order(db, user_id: str, data: dict) -> dict:
    # if a delivery address is given, make sure it actually belongs to this user
    if data.get("delivery_address_id"):
        user = await db.users.find_one({"_id": _to_object_id(user_id, "user id")})
        if not user or not any(
            a["_id"] == data["delivery_address_id"] for a in user.get("addresses", [])
        ):
            raise BadRequestException("Invalid delivery address")

    now = datetime.utcnow()
    doc = {
        "request_number": _generate_request_number(),
        "user_id": user_id,
        "occasion": data["occasion"],
        "flavor": data["flavor"],
        "size": data["size"],
        "shape": data.get("shape"),
        "message_on_cake": data.get("message_on_cake"),
        "reference_images": data.get("reference_images", []),
        "description": data["description"],
        "budget_min": data.get("budget_min"),
        "budget_max": data.get("budget_max"),
        "needed_by": data["needed_by"],
        "contact_phone": data["contact_phone"],
        "delivery_address_id": data.get("delivery_address_id"),
        "status": "pending",
        "quoted_price": None,
        "admin_note": None,
        "status_history": [{"status": "pending", "timestamp": now, "note": "Request submitted"}],
        "created_at": now,
        "updated_at": now,
    }
    result = await db.custom_orders.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _out(doc)


# ── LIST MY REQUESTS ──────────────────────────────────────────
async def list_custom_orders(db, user_id: str, page: int = 1, limit: int = 10) -> dict:
    page = max(page, 1)
    limit = min(max(limit, 1), 50)
    skip = (page - 1) * limit

    query = {"user_id": user_id}
    total = await db.custom_orders.count_documents(query)
    cursor = db.custom_orders.find(query).sort([("created_at", -1)]).skip(skip).limit(limit)
    items = [_out(doc) async for doc in cursor]

    return {
        "items": items,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total else 0,
        },
    }


# ── GET SINGLE (ownership enforced) ───────────────────────────
async def get_custom_order(db, user_id: str, request_id: str) -> dict:
    doc = await db.custom_orders.find_one({
        "_id": _to_object_id(request_id, "request id"),
        "user_id": user_id,
    })
    if not doc:
        raise NotFoundException("Custom order request not found")
    return _out(doc)


async def accept_quote(db, user_id: str, request_id: str) -> dict:
    doc = await get_custom_order(db, user_id, request_id)   # already enforces ownership

    if doc["status"] != "quoted":
        raise BadRequestException("This request doesn't have a pending quote to accept")

    now = datetime.utcnow()
    await db.custom_orders.update_one(
        {"_id": _to_object_id(request_id)},
        {
            "$set": {"status": "confirmed", "updated_at": now},
            "$push": {"status_history": {"status": "confirmed", "timestamp": now, "note": "Accepted by customer"}},
        },
    )
    return await get_custom_order(db, user_id, request_id)