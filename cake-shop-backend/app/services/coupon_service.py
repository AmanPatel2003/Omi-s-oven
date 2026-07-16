from datetime import datetime

from app.core.exceptions import NotFoundException, BadRequestException


async def check_coupon_eligibility(db, code: str, subtotal: float) -> dict:
    """
    Shared eligibility logic — used by both /coupons/validate and
    cart_service.apply_coupon, so the two never drift out of sync.
    Raises BadRequestException/NotFoundException on failure, otherwise
    returns the coupon doc plus the computed discount amount for this subtotal.
    """
    coupon = await db.coupons.find_one({"code": code, "is_active": True})
    if not coupon:
        raise NotFoundException("Invalid or expired coupon code")

    if coupon.get("expires_at") and coupon["expires_at"] < datetime.utcnow():
        raise BadRequestException("This coupon has expired")

    if coupon.get("usage_limit") is not None and coupon.get("used_count", 0) >= coupon["usage_limit"]:
        raise BadRequestException("This coupon has reached its usage limit")

    if subtotal < coupon.get("min_order_value", 0):
        raise BadRequestException(f"Minimum order value for this coupon is ₹{coupon['min_order_value']}")

    if coupon["discount_type"] == "percentage":
        discount = subtotal * (coupon["discount_value"] / 100)
        if coupon.get("max_discount"):
            discount = min(discount, coupon["max_discount"])
    else:  # flat
        discount = coupon["discount_value"]
    discount = min(round(discount, 2), subtotal)

    return {"coupon": coupon, "discount_amount": discount}


# ── VALIDATE (does not apply — just checks + previews discount) ────
async def validate_coupon(db, user_id: str, code: str) -> dict:
    from app.services import cart_service   # local import avoids circular import with cart_service

    cart_data = await cart_service.get_cart(db, user_id)
    if not cart_data["items"]:
        return {
            "valid": False,
            "code": code,
            "discount_type": None,
            "discount_value": None,
            "discount_amount": None,
            "message": "Your cart is empty",
        }

    subtotal = sum(it["line_total"] for it in cart_data["items"])

    try:
        result = await check_coupon_eligibility(db, code, subtotal)
    except (NotFoundException, BadRequestException) as e:
        return {
            "valid": False,
            "code": code,
            "discount_type": None,
            "discount_value": None,
            "discount_amount": None,
            "message": str(e.detail) if hasattr(e, "detail") else str(e),
        }

    coupon = result["coupon"]
    return {
        "valid": True,
        "code": code,
        "discount_type": coupon["discount_type"],
        "discount_value": coupon["discount_value"],
        "discount_amount": result["discount_amount"],
        "message": f"You save ₹{result['discount_amount']} with this code",
    }


# ── LIST ACTIVE PUBLIC COUPONS ───────────────────────────────────
async def list_active_coupons(db) -> list:
    now = datetime.utcnow()
    cursor = db.coupons.find({
        "is_active": True,
        "is_public": True,
        "$or": [
            {"expires_at": None},
            {"expires_at": {"$gt": now}},
        ],
    }).sort([("discount_value", -1)])

    coupons = []
    async for c in cursor:
        # hide codes that are technically active but have hit their usage cap —
        # no point advertising a code nobody can actually redeem
        if c.get("usage_limit") is not None and c.get("used_count", 0) >= c["usage_limit"]:
            continue
        coupons.append({
            "code": c["code"],
            "description": c.get("description"),
            "discount_type": c["discount_type"],
            "discount_value": c["discount_value"],
            "max_discount": c.get("max_discount"),
            "min_order_value": c.get("min_order_value", 0),
            "expires_at": c.get("expires_at"),
        })
    return coupons

