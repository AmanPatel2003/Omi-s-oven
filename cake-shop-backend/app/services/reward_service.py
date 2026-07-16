from datetime import datetime
from bson import ObjectId

from app.core.exceptions import NotFoundException, BadRequestException
from app.config import settings



def _to_object_id(id_str: str, label: str = "id"):
    try:
        return ObjectId(id_str)
    except Exception:
        raise BadRequestException(f"Invalid {label}")


async def _get_or_create_reward(db, user_id: str) -> dict:
    reward = await db.rewards.find_one({"user_id": user_id})
    if not reward:
        # NOTE: register_user already inserts this doc on signup — this is
        # just a safety net for older accounts or google-login users if
        # that insert was ever skipped.
        now = datetime.utcnow()
        reward = {
            "user_id": user_id,
            "total_points": 0,
            "lifetime_points": 0,
            "transactions": [],
            "created_at": now,
            "updated_at": now,
        }
        result = await db.rewards.insert_one(reward)
        reward["_id"] = result.inserted_id
    return reward


def _get_tier(lifetime_points: int) -> dict:
    current = settings.TIERS[0]
    for tier in settings.TIERS:
        if lifetime_points >= tier["min_lifetime_points"]:
            current = tier
    return current


def _get_next_tier(lifetime_points: int) -> dict | None:
    for tier in settings.TIERS:
        if lifetime_points < tier["min_lifetime_points"]:
            return tier
    return None


# ── BALANCE + TIER ────────────────────────────────────────────
async def get_balance(db, user_id: str) -> dict:
    reward = await _get_or_create_reward(db, user_id)
    current_tier = _get_tier(reward["lifetime_points"])
    next_tier = _get_next_tier(reward["lifetime_points"])

    cart = await db.carts.find_one({"user_id": user_id})
    redeemed = cart.get("redeemed_points", 0) if cart else 0

    return {
        "total_points": reward["total_points"],
        "lifetime_points": reward["lifetime_points"],
        "current_tier": current_tier["name"],
        "next_tier": next_tier["name"] if next_tier else None,
        "points_to_next_tier": (
            next_tier["min_lifetime_points"] - reward["lifetime_points"] if next_tier else None
        ),
        "redeemed_points_on_cart": redeemed,
        "redeemed_value_on_cart": round(redeemed * settings.POINTS_TO_RUPEE_RATE, 2),
    }


# ── settings.TIERS INFO (static, no auth needed) ────────────────────────
def get_TIERS_info() -> dict:
    return {
        "settings.TIERS": settings.TIERS,
        "point_value": f"1 point = ₹{settings.POINTS_TO_RUPEE_RATE}",
    }


# ── TRANSACTION HISTORY ─────────────────────────────────────────
async def list_transactions(db, user_id: str, page: int = 1, limit: int = 20) -> dict:
    reward = await _get_or_create_reward(db, user_id)
    all_txns = sorted(reward.get("transactions", []), key=lambda t: t["created_at"], reverse=True)

    page = max(page, 1)
    limit = min(max(limit, 1), 100)
    start = (page - 1) * limit
    end = start + limit
    items = all_txns[start:end]
    total = len(all_txns)

    return {
        "items": items,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total else 0,
        },
    }


# ── REDEEM AT CHECKOUT (holds points against the cart) ──────────
async def redeem_points(db, user_id: str, points: int) -> dict:
    if points < MIN_REDEEM_POINTS:
        raise BadRequestException(f"Minimum {MIN_REDEEM_POINTS} points required to redeem")

    reward = await _get_or_create_reward(db, user_id)
    if reward["total_points"] < points:
        raise BadRequestException("Insufficient points balance")

    # need the cart's current subtotal to cap redemption at MAX_REDEEM_PERCENT_OF_ORDER
    from app.services import cart_service
    cart_data = await cart_service.get_cart(db, user_id)
    if not cart_data["items"]:
        raise BadRequestException("Your cart is empty")

    subtotal = sum(it["line_total"] for it in cart_data["items"])
    max_redeemable_value = subtotal * MAX_REDEEM_PERCENT_OF_ORDER
    redeem_value = points * settings.POINTS_TO_RUPEE_RATE

    if redeem_value > max_redeemable_value:
        max_points = int(max_redeemable_value / settings.POINTS_TO_RUPEE_RATE)
        raise BadRequestException(
            f"You can redeem at most {max_points} points ({int(MAX_REDEEM_PERCENT_OF_ORDER*100)}% of order value) on this order"
        )

    # store as a hold on the cart — not deducted from balance until order is placed
    await db.carts.update_one(
        {"user_id": user_id},
        {"$set": {"redeemed_points": points, "updated_at": datetime.utcnow()}},
        upsert=True,
    )

    return {
        "redeemed_points": points,
        "discount_value": round(redeem_value, 2),
        "remaining_balance": reward["total_points"] - points,  # projected, not yet committed
    }


# ── INTERNAL: called from order_service.place_order ──────────────
async def commit_redemption(db, user_id: str, order_id: str, points: int):
    """Actually deduct points from balance once an order is placed."""
    if points <= 0:
        return
    now = datetime.utcnow()
    txn = {
        "type": "redeem",
        "points": -points,
        "order_id": order_id,
        "description": f"Redeemed on order {order_id}",
        "created_at": now,
    }
    await db.rewards.update_one(
        {"user_id": user_id},
        {"$inc": {"total_points": -points}, "$push": {"transactions": txn}, "$set": {"updated_at": now}},
    )


# ── INTERNAL: called from payment_service on payment.captured ────
async def award_points(db, user_id: str, order_id: str, order_total: float):
    """Award points once payment is actually confirmed (not just order placed)."""
    points_earned = int(order_total * settings.POINTS_EARN_RATE)
    if points_earned <= 0:
        return
    now = datetime.utcnow()
    txn = {
        "type": "earn",
        "points": points_earned,
        "order_id": order_id,
        "description": f"Earned on order {order_id}",
        "created_at": now,
    }
    await db.rewards.update_one(
        {"user_id": user_id},
        {
            "$inc": {"total_points": points_earned, "lifetime_points": points_earned},
            "$push": {"transactions": txn},
            "$set": {"updated_at": now},
        },
        upsert=True,
    )