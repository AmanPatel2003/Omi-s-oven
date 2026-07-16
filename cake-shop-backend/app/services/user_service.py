from datetime import datetime
from typing import Optional

from bson import ObjectId

from app.core.exceptions import ConflictException, NotFoundException
from app.core.security import verify_password, hash_password
from app.utils.helpers import serialize_doc


def _to_object_id(user_id: str):
    try:
        return ObjectId(user_id)
    except Exception:
        return user_id  # fall back to raw string if not a valid ObjectId


async def _find_user(db, user_id: str) -> dict:
    oid = _to_object_id(user_id)
    user = await db.users.find_one({"_id": oid})
    if not user:
        raise NotFoundException("User not found")
    return user


# ── UPDATE PROFILE ────────────────────────────────────────────
async def update_profile(
    db,
    user_id: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> dict:
    user = await _find_user(db, user_id)

    update_data = {}
    if name is not None:
        update_data["name"] = name.strip()
    if email is not None:
        email = email.lower().strip()
        if email != user.get("email"):
            existing = await db.users.find_one({"email": email})
            if existing and str(existing["_id"]) != str(user["_id"]):
                raise ConflictException("An account with this email already exists")
        update_data["email"] = email
    if phone is not None:
        phone = phone.strip()
        if phone != user.get("phone"):
            existing = await db.users.find_one({"phone": phone})
            if existing and str(existing["_id"]) != str(user["_id"]):
                raise ConflictException("An account with this phone number already exists")
        update_data["phone"] = phone

    if not update_data:
        raise ValueError("No fields to update")

    update_data["updated_at"] = datetime.utcnow()

    result = await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": update_data},
    )

    if result.matched_count == 0:
        raise NotFoundException("User not found")

    updated_user = await db.users.find_one({"_id": user["_id"]})
    updated_user["id"] = str(updated_user.pop("_id"))
    updated_user.pop("password_hash", None)
    return updated_user


# ── CHANGE PASSWORD ───────────────────────────────────────────
async def change_password(
    db,
    user_id: str,
    current_password: str,
    new_password: str,
) -> bool:
    user = await _find_user(db, user_id)

    if not verify_password(current_password, user["password_hash"]):
        raise ConflictException("Current password is incorrect")

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "password_hash": hash_password(new_password),
            "updated_at": datetime.utcnow(),
        }},
    )
    return True


# ── ADDRESSES ──────────────────────────────────────────────────
async def list_addresses(db, user_id: str) -> list:
    user = await _find_user(db, user_id)
    return [serialize_doc(a) for a in user.get("addresses", [])]


async def add_address(db, user_id: str, address: dict) -> dict:
    user = await _find_user(db, user_id)

    new_address = {
        "_id": str(ObjectId()),
        **address,
        "is_default": len(user.get("addresses", [])) == 0,  # first address = default
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$push": {"addresses": new_address}, "$set": {"updated_at": datetime.utcnow()}},
    )
    return new_address


async def update_address(db, user_id: str, address_id: str, address: dict) -> dict:
    user = await _find_user(db, user_id)
    addresses = user.get("addresses", [])

    idx = next((i for i, a in enumerate(addresses) if a["_id"] == address_id), None)
    if idx is None:
        raise NotFoundException("Address not found")

    updated = {**addresses[idx], **address, "updated_at": datetime.utcnow()}
    addresses[idx] = updated

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"addresses": addresses, "updated_at": datetime.utcnow()}},
    )
    return updated


async def delete_address(db, user_id: str, address_id: str) -> bool:
    user = await _find_user(db, user_id)
    addresses = user.get("addresses", [])

    if not any(a["_id"] == address_id for a in addresses):
        raise NotFoundException("Address not found")

    remaining = [a for a in addresses if a["_id"] != address_id]

    # if we deleted the default and others remain, promote the first one
    if remaining and not any(a.get("is_default") for a in remaining):
        remaining[0]["is_default"] = True

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"addresses": remaining, "updated_at": datetime.utcnow()}},
    )
    return True


async def set_default_address(db, user_id: str, address_id: str) -> dict:
    user = await _find_user(db, user_id)
    addresses = user.get("addresses", [])

    if not any(a["_id"] == address_id for a in addresses):
        raise NotFoundException("Address not found")

    for a in addresses:
        a["is_default"] = (a["_id"] == address_id)

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"addresses": addresses, "updated_at": datetime.utcnow()}},
    )
    return next(a for a in addresses if a["_id"] == address_id)