from datetime import datetime
from typing import Optional
from bson import ObjectId

from app.core.exceptions import NotFoundException, BadRequestException
from app.utils.helpers import serialize_doc

# ── CONFIG (move to settings/config.py when you have per-city rules etc.) ──
TAX_RATE = 0.05                 # 5% GST-style flat tax on (subtotal - discount)
DELIVERY_FEE = 49.0
FREE_DELIVERY_THRESHOLD = 999.0


def _to_object_id(id_str: str):
    try:
        return ObjectId(id_str)
    except Exception:
        raise BadRequestException("Invalid product id")


async def _get_or_create_cart(db, user_id: str) -> dict:
    cart = await db.carts.find_one({"user_id": user_id})
    if not cart:
        cart = {
            "user_id": user_id,
            "items": [],
            "applied_coupon": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        result = await db.carts.insert_one(cart)
        cart["_id"] = result.inserted_id
    return cart


def _get_variant_price_and_stock(product: dict, variant_name: Optional[str]):
    """
    Returns (price, stock) for the given variant, or base product
    price/stock if no variant is specified or product has none.
    """
    variants = product.get("variants") or []
    if variant_name and variants:
        variant = next((v for v in variants if v["name"] == variant_name), None)
        if not variant:
            raise BadRequestException(f"Variant '{variant_name}' not found for this product")
        return variant["price"], variant["stock"]
    return product.get("discount_price") or product["price"], product.get("stock", 0)


# ── ADD ITEM ──────────────────────────────────────────────────
async def add_item(db, user_id: str, product_id: str, variant_name: Optional[str], qty: int) -> dict:
    oid = _to_object_id(product_id)
    product = await db.products.find_one({"_id": oid, "is_available": True})
    if not product:
        raise NotFoundException("Product not found")

    _, stock = _get_variant_price_and_stock(product, variant_name)
    if stock < qty:
        raise BadRequestException(f"Only {stock} item(s) left in stock")

    cart = await _get_or_create_cart(db, user_id)

    existing_idx = next(
        (i for i, it in enumerate(cart["items"])
         if it["product_id"] == product_id and it.get("variant_name") == variant_name),
        None,
    )

    if existing_idx is not None:
        new_qty = cart["items"][existing_idx]["qty"] + qty
        if new_qty > stock:
            raise BadRequestException(f"Only {stock} item(s) left in stock")
        cart["items"][existing_idx]["qty"] = new_qty
    else:
        cart["items"].append({"product_id": product_id, "variant_name": variant_name, "qty": qty})

    await db.carts.update_one(
        {"_id": cart["_id"]},
        {"$set": {"items": cart["items"], "updated_at": datetime.utcnow()}},
    )
    return await get_cart(db, user_id)


# ── UPDATE ITEM QTY ───────────────────────────────────────────
async def update_item(db, user_id: str, product_id: str, variant_name: Optional[str], qty: int) -> dict:
    cart = await _get_or_create_cart(db, user_id)

    idx = next(
        (i for i, it in enumerate(cart["items"])
         if it["product_id"] == product_id and it.get("variant_name") == variant_name),
        None,
    )
    if idx is None:
        raise NotFoundException("Item not found in cart")

    if qty == 0:
        cart["items"].pop(idx)
    else:
        oid = _to_object_id(product_id)
        product = await db.products.find_one({"_id": oid, "is_available": True})
        if not product:
            raise NotFoundException("Product not found")
        _, stock = _get_variant_price_and_stock(product, variant_name)
        if qty > stock:
            raise BadRequestException(f"Only {stock} item(s) left in stock")
        cart["items"][idx]["qty"] = qty

    await db.carts.update_one(
        {"_id": cart["_id"]},
        {"$set": {"items": cart["items"], "updated_at": datetime.utcnow()}},
    )
    return await get_cart(db, user_id)


# ── REMOVE ITEM ───────────────────────────────────────────────
async def remove_item(db, user_id: str, product_id: str, variant_name: Optional[str] = None) -> dict:
    cart = await _get_or_create_cart(db, user_id)

    new_items = [
        it for it in cart["items"]
        if not (it["product_id"] == product_id and it.get("variant_name") == variant_name)
    ]
    if len(new_items) == len(cart["items"]):
        raise NotFoundException("Item not found in cart")

    await db.carts.update_one(
        {"_id": cart["_id"]},
        {"$set": {"items": new_items, "updated_at": datetime.utcnow()}},
    )
    return await get_cart(db, user_id)


# ── CLEAR CART ────────────────────────────────────────────────
async def clear_cart(db, user_id: str) -> dict:
    cart = await _get_or_create_cart(db, user_id)
    await db.carts.update_one(
        {"_id": cart["_id"]},
        {"$set": {"items": [], "applied_coupon": None, "updated_at": datetime.utcnow()}},
    )
    return await get_cart(db, user_id)


# ── GET CART (enriched with live product data) ────────────────
async def get_cart(db, user_id: str) -> dict:
    cart = await _get_or_create_cart(db, user_id)

    enriched_items = []
    for item in cart["items"]:
        try:
            oid = ObjectId(item["product_id"])
        except Exception:
            continue  # skip corrupt entries rather than crash the whole cart

        product = await db.products.find_one({"_id": oid})
        if not product or not product.get("is_available", True):
            continue  # product removed/deactivated — silently skip (or flag, see note below)

        price, stock = _get_variant_price_and_stock(product, item.get("variant_name"))
        qty = item["qty"]

        enriched_items.append({
            "product_id": item["product_id"],
            "variant_name": item.get("variant_name"),
            "name": product["name"],
            "image": product["images"][0] if product.get("images") else None,
            "price": price,
            "qty": qty,
            "line_total": round(price * qty, 2),
            "in_stock": stock >= qty,
            "available_stock": stock,
        })

    return {
        "items": enriched_items,
        "applied_coupon": cart.get("applied_coupon"),
        "item_count": sum(it["qty"] for it in enriched_items),
    }


# ── COUPONS ───────────────────────────────────────────────────
async def apply_coupon(db, user_id: str, code: str) -> dict:
    from app.services import coupon_service   # local import — avoids circular import, see below

    cart_data = await get_cart(db, user_id)
    subtotal = sum(it["line_total"] for it in cart_data["items"])

    await coupon_service.check_coupon_eligibility(db, code, subtotal)

    cart = await _get_or_create_cart(db, user_id)
    await db.carts.update_one(
        {"_id": cart["_id"]},
        {"$set": {"applied_coupon": code, "updated_at": datetime.utcnow()}},
    )
    return await get_cart(db, user_id)


async def remove_coupon(db, user_id: str) -> dict:
    cart = await _get_or_create_cart(db, user_id)
    await db.carts.update_one(
        {"_id": cart["_id"]},
        {"$set": {"applied_coupon": None, "updated_at": datetime.utcnow()}},
    )
    return await get_cart(db, user_id)


# ── CART SUMMARY (tax, delivery, discount, total) ─────────────
async def get_cart_summary(db, user_id: str) -> dict:
    cart_data = await get_cart(db, user_id)
    items = cart_data["items"]

    subtotal = round(sum(it["line_total"] for it in items), 2)

    discount = 0.0
    coupon_code = cart_data.get("applied_coupon")
    if coupon_code:
        coupon = await db.coupons.find_one({"code": coupon_code, "is_available": True})
        if coupon and subtotal >= coupon.get("min_order_value", 0):
            if coupon["discount_type"] == "percentage":
                discount = subtotal * (coupon["discount_value"] / 100)
                if coupon.get("max_discount"):
                    discount = min(discount, coupon["max_discount"])
            else:  # flat
                discount = coupon["discount_value"]
            discount = min(discount, subtotal)  # never discount below zero
        else:
            # coupon became invalid (e.g. cart dropped below min order) — silently drop it
            coupon_code = None

    taxable_amount = subtotal - discount
    tax = round(taxable_amount * TAX_RATE, 2)
    delivery_fee = 0.0 if taxable_amount >= FREE_DELIVERY_THRESHOLD or not items else DELIVERY_FEE
    total = round(taxable_amount + tax + delivery_fee, 2)

    return {
        "subtotal": subtotal,
        "discount": round(discount, 2),
        "tax": tax,
        "delivery_fee": delivery_fee,
        "total": total,
        "applied_coupon": coupon_code,
        "item_count": cart_data["item_count"],
    }