# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FILE: app/services/auth_service.py
# PURPOSE: All auth business logic.
#          Routes in api/v1/auth.py call these functions.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import datetime

from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.core.exceptions import (
    ConflictException, UnauthorizedException, NotFoundException,
)
from app.models.user import new_user
from app.utils.helpers import serialize_doc
from app.config import settings


# ── REGISTER ──────────────────────────────────────────────────
async def register_user(
    db: AsyncIOMotorDatabase,
    name: str,
    email: str,
    phone: str,
    password: str,
    role: str = "customer",
    is_active: bool = True,
    created_at: datetime = None,
    updated_at: datetime = None,
) -> dict:
    """
    Create a new user account.
    Raises ConflictException if email or phone already exists.
    """

    # Check email not taken
    if await db.users.find_one({"email": email.lower().strip()}):
        raise ConflictException("An account with this email already exists")

    # Check phone not taken
    if await db.users.find_one({"phone": phone.strip()}):
        raise ConflictException("An account with this phone number already exists")

    # Build and insert document
    doc = new_user(
        name=name,
        email=email,
        phone=phone,
        password_hash=hash_password(password),
        role=role,
        is_active=is_active,
        created_at=created_at,
        updated_at=updated_at,
    )
    print("doc", doc)
    result = await db.users.insert_one(doc.model_dump())
    user_id = str(result.inserted_id)

    # Create empty rewards doc for new user
    await db.rewards.insert_one({
        "user_id": user_id,
        "total_points": 0,
        "lifetime_points": 0,
        "transactions": [],
        "created_at": datetime.utcnow(),
    })

    tokens = _build_tokens(user_id, role)
    return {**tokens, "user": _user_out(user_id, name, email, phone, role)}


# ── LOGIN ─────────────────────────────────────────────────────
async def login_user(
    db: AsyncIOMotorDatabase,
    identifier: str,
    password: str,
) -> dict:
    """
    Login with email OR phone + password.
    Returns tokens + user info.
    """
    identifier = identifier.strip()

    user = await db.users.find_one({
        "$or": [
            {"email": identifier.lower()},
            {"phone": identifier},
        ]
    })

    # Use same error message for both cases — don't reveal which field is wrong
    if not user or not verify_password(password, user["password_hash"]):
        raise UnauthorizedException("Invalid credentials")

    if not user.get("is_active", True):
        raise UnauthorizedException("Account is deactivated. Contact support.")

    user_id = str(user["_id"])
    role = user.get("role", "customer")

    tokens = _build_tokens(user_id, role)
    return {
        **tokens,
        "user": _user_out(
            user_id,
            user["name"],
            user["email"],
            user["phone"],
            role,
            user.get("loyalty_tier", "silver"),
            user.get("reward_points", 0),
        ),
    }


async def google_login_user(
    db: AsyncIOMotorDatabase,
    token: str,
) -> dict:

    try:
        google_user = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )

    except Exception:
        raise UnauthorizedException(
            "Invalid Google token"
        )

    email = google_user["email"]

    user = await db.users.find_one({
        "email": email
    })

    # Create account if first login
    if not user:

        user_doc = {
            "name": google_user.get("name"),
            "email": email,
            "phone": "",
            "role": "customer",
            "google_id": google_user.get("sub"),
            "picture": google_user.get("picture"),
            "auth_provider": "google",
            "is_active": True,
            "reward_points": 0,
            "loyalty_tier": "silver",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = await db.users.insert_one(user_doc)

        user_id = str(result.inserted_id)

        await db.rewards.insert_one({
            "user_id": user_id,
            "total_points": 0,
            "lifetime_points": 0,
            "transactions": [],
            "created_at": datetime.utcnow(),
        })

        user = await db.users.find_one({
            "_id": result.inserted_id
        })

    if not user.get("is_active", True):
        raise UnauthorizedException(
            "Account is deactivated"
        )

    user_id = str(user["_id"])
    role = user.get("role", "customer")

    tokens = _build_tokens(
        user_id=user_id,
        role=role
    )

    return {
        **tokens,
        "user": {
            "id": user_id,
            "name": user.get("name"),
            "email": user.get("email"),
            "phone": user.get("phone", ""),
            "role": role,
            "picture": user.get("picture"),
            "loyalty_tier": user.get("loyalty_tier", "silver"),
            "reward_points": user.get("reward_points", 0),
        }
    }

# ── REFRESH TOKEN ─────────────────────────────────────────────
async def refresh_access_token(
    db: AsyncIOMotorDatabase,
    refresh_token: str,
) -> dict:
    """
    Exchange valid refresh token → new access + refresh token pair.
    Called automatically by frontend axios interceptor on 401.
    """
    payload = decode_token(refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedException("Invalid or expired refresh token")

    user_id = payload.get("sub")

    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        user = await db.users.find_one({"_id": user_id})

    if not user or not user.get("is_active", True):
        raise UnauthorizedException("User not found")

    return _build_tokens(str(user["_id"]), user.get("role", "customer"))


# ── GET CURRENT USER (GET /auth/me) ──────────────────────────
async def get_me(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> dict:
    """Return full profile of the logged-in user."""
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        user = await db.users.find_one({"_id": user_id})

    if not user:
        raise NotFoundException("User not found")

    return serialize_doc(user)


# ── CHANGE PASSWORD ───────────────────────────────────────────
async def change_password(
    db: AsyncIOMotorDatabase,
    user_id: str,
    old_password: str,
    new_password: str,
) -> bool:
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        user = await db.users.find_one({"_id": user_id})

    if not user:
        raise NotFoundException("User not found")

    if not verify_password(old_password, user["password_hash"]):
        raise UnauthorizedException("Current password is incorrect")

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "password_hash": hash_password(new_password),
            "updated_at": datetime.utcnow(),
        }},
    )
    return True


# ── PRIVATE HELPERS ───────────────────────────────────────────
def _build_tokens(user_id: str, role: str) -> dict:
    data = {"sub": user_id, "role": role}
    return {
        "access_token": create_access_token(data),
        "refresh_token": create_refresh_token(data),
        "token_type": "bearer",
    }


def _user_out(
    user_id, name, email, phone, role,
    loyalty_tier="silver", reward_points=0,
) -> dict:
    return {
        "id": user_id,
        "name": name,
        "email": email,
        "phone": phone,
        "role": role,
        "loyalty_tier": loyalty_tier,
        "reward_points": reward_points,
    }
    
 