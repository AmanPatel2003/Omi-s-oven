from datetime import datetime
from bson import ObjectId

from app.core.exceptions import NotFoundException, BadRequestException
from app.schemas.admin_custom_order import VALID_TRANSITIONS
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
    "reviewing": ("Request under review", "We're reviewing your custom cake request."),
    "quoted": ("Your quote is ready", "We've prepared a quote for your custom cake request."),
    "confirmed": ("Order confirmed", "Your custom cake order has been confirmed."),
    "in_progress": ("We're baking!", "Work has started on your custom cake."),
    "completed": ("Custom cake ready", "Your custom cake request has been completed."),
    "rejected": ("Request declined", "Unfortunately we're unable to fulfill this request."),
    "cancelled": ("Request cancelled", "Your custom cake request has been cancelled."),
}


# ── LIST ALL ──────────────────────────────────────────────────────
async def list_custom_orders(db, status: str | None = None, page: int = 1, limit: int = 20) -> dict:
    query = {}
    if status:
        query["status"] = status

    page = max(page, 1)
    limit = min(max(limit, 1), 100)
    skip = (page - 1) * limit

    total = await db.custom_orders.count_documents(query)
    cursor = db.custom_orders.find(query).sort([("created_at", -1)]).skip(skip).limit(limit)

    items = []
    async for doc in cursor:
        items.append({
            "id": str(doc["_id"]),
            "request_number": doc["request_number"],
            "customer_name": doc.get("customer_name", ""),
            "contact_phone": doc["contact_phone"],
            "occasion": doc["occasion"],
            "needed_by": doc["needed_by"],
            "status": doc["status"],
            "quoted_price": doc.get("quoted_price"),
            "created_at": doc["created_at"],
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
async def get_custom_order(db, request_id: str) -> dict:
    oid = _to_object_id(request_id, "request id")
    doc = await db.custom_orders.find_one({"_id": oid})
    if not doc:
        raise NotFoundException("Custom order request not found")

    user = await db.users.find_one({"_id": ObjectId(doc["user_id"])})
    doc["customer_name"] = user["name"] if user else "Unknown"
    doc["customer_email"] = user["email"] if user else ""

    return _out(doc)


# ── UPDATE STATUS ──────────────────────────────────────────────────────
async def update_status(db, request_id: str, new_status: str, admin_note: str | None) -> dict:
    oid = _to_object_id(request_id, "request id")
    doc = await db.custom_orders.find_one({"_id": oid})
    if not doc:
        raise NotFoundException("Custom order request not found")

    current_status = doc["status"]
    allowed_next = VALID_TRANSITIONS.get(current_status, [])
    if new_status not in allowed_next:
        raise BadRequestException(
            f"Cannot move request from '{current_status}' to '{new_status}'. "
            f"Allowed next states: {', '.join(allowed_next) or 'none — this is a final status'}"
        )

    if new_status == "confirmed" and not doc.get("quoted_price"):
        raise BadRequestException("Cannot confirm a request that hasn't been quoted yet")

    now = datetime.utcnow()
    update_fields = {"status": new_status, "updated_at": now}
    if admin_note:
        update_fields["admin_note"] = admin_note

    await db.custom_orders.update_one(
        {"_id": oid},
        {
            "$set": update_fields,
            "$push": {"status_history": {"status": new_status, "timestamp": now, "note": admin_note}},
        },
    )

    title, message = STATUS_MESSAGES.get(new_status, (f"Request {new_status}", f"Status updated to {new_status}."))
    await notification_service.create_notification(
        db, doc["user_id"], f"custom_order_{new_status}", title, message, reference_id=request_id,
    )

    return await get_custom_order(db, request_id)


# ── SET QUOTE ─────────────────────────────────────────────────────────
async def set_quote(db, request_id: str, quoted_price: float, admin_note: str | None) -> dict:
    oid = _to_object_id(request_id, "request id")
    doc = await db.custom_orders.find_one({"_id": oid})
    if not doc:
        raise NotFoundException("Custom order request not found")

    if doc["status"] not in ("pending", "reviewing"):
        raise BadRequestException(
            f"Cannot set a quote while request is '{doc['status']}'. "
            f"Move it to 'reviewing' first, or it may already be quoted."
        )

    now = datetime.utcnow()
    await db.custom_orders.update_one(
        {"_id": oid},
        {
            "$set": {
                "quoted_price": quoted_price,
                "status": "quoted",
                "admin_note": admin_note,
                "updated_at": now,
            },
            "$push": {"status_history": {
                "status": "quoted", "timestamp": now,
                "note": admin_note or f"Quoted ₹{quoted_price}",
            }},
        },
    )

    await notification_service.create_notification(
        db, doc["user_id"], "custom_order_quoted",
        "Your quote is ready", f"We've quoted ₹{quoted_price} for your custom cake request. Please review and confirm.",
        reference_id=request_id,
    )

    return await get_custom_order(db, request_id)