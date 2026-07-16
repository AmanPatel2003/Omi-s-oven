from datetime import datetime
from bson import ObjectId

from app.core.exceptions import NotFoundException, BadRequestException


def _to_object_id(id_str: str, label: str = "id"):
    try:
        return ObjectId(id_str)
    except Exception:
        raise BadRequestException(f"Invalid {label}")


def _out(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


# ── INTERNAL: called by other services (orders, payments, delivery, rewards) ──
async def create_notification(
    db,
    user_id: str,
    type: str,
    title: str,
    message: str,
    reference_id: str | None = None,
) -> None:
    """
    Fire-and-forget in-app notification record.
    Does NOT send email/SMS/WhatsApp itself — that's a separate dispatch
    step (see note below) that should check user preferences before sending.
    """
    await db.notifications.insert_one({
        "user_id": user_id,
        "type": type,
        "title": title,
        "message": message,
        "reference_id": reference_id,
        "is_read": False,
        "created_at": datetime.utcnow(),
    })


# ── LIST MY NOTIFICATIONS ────────────────────────────────────────
async def list_notifications(db, user_id: str, page: int = 1, limit: int = 20) -> dict:
    page = max(page, 1)
    limit = min(max(limit, 1), 100)
    skip = (page - 1) * limit

    query = {"user_id": user_id}
    total = await db.notifications.count_documents(query)
    unread_count = await db.notifications.count_documents({"user_id": user_id, "is_read": False})

    cursor = db.notifications.find(query).sort([("created_at", -1)]).skip(skip).limit(limit)
    items = [_out(doc) async for doc in cursor]

    return {
        "items": items,
        "unread_count": unread_count,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total else 0,
        },
    }


# ── MARK ONE AS READ ──────────────────────────────────────────────
async def mark_as_read(db, user_id: str, notification_id: str) -> dict:
    oid = _to_object_id(notification_id, "notification id")
    result = await db.notifications.update_one(
        {"_id": oid, "user_id": user_id},   # ownership check baked into the filter
        {"$set": {"is_read": True}},
    )
    if result.matched_count == 0:
        raise NotFoundException("Notification not found")

    doc = await db.notifications.find_one({"_id": oid})
    return _out(doc)


# ── MARK ALL AS READ ──────────────────────────────────────────────
async def mark_all_as_read(db, user_id: str) -> dict:
    result = await db.notifications.update_many(
        {"user_id": user_id, "is_read": False},
        {"$set": {"is_read": True}},
    )
    return {"marked_read": result.modified_count}


# ── PREFERENCES ────────────────────────────────────────────────────
async def get_preferences(db, user_id: str) -> dict:
    user = await db.users.find_one({"_id": _to_object_id(user_id, "user id")})
    if not user:
        raise NotFoundException("User not found")

    # default if never set
    return user.get("notification_preferences", {"email": True, "sms": True, "whatsapp": False})


async def update_preferences(db, user_id: str, email=None, sms=None, whatsapp=None) -> dict:
    current = await get_preferences(db, user_id)

    if email is not None:
        current["email"] = email
    if sms is not None:
        current["sms"] = sms
    if whatsapp is not None:
        current["whatsapp"] = whatsapp

    await db.users.update_one(
        {"_id": _to_object_id(user_id, "user id")},
        {"$set": {"notification_preferences": current, "updated_at": datetime.utcnow()}},
    )
    return current