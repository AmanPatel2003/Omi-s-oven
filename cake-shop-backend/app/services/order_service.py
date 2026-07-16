import random
import string
from datetime import datetime, timedelta
from typing import Optional
from bson import ObjectId

from app.core.exceptions import NotFoundException, BadRequestException
from app.services import cart_service

ACTIVE_STATUSES = ["pending", "confirmed", "preparing", "out_for_delivery"]
CANCELLABLE_STATUSES = ["pending", "confirmed"]
DELIVERY_ESTIMATE_HOURS = 48


def _to_object_id(id_str: str, label: str = "id"):
    try:
        return ObjectId(id_str)
    except Exception:
        raise BadRequestException(f"Invalid {label}")


def _generate_order_number() -> str:
    date_part = datetime.utcnow().strftime("%Y%m%d")
    rand_part = "".join(random.choices(string.digits, k=4))
    return f"ORD-{date_part}-{rand_part}"


def _out(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


# ── PLACE ORDER ───────────────────────────────────────────────
async def place_order(
    db,
    user_id: str,
    address_id: str,
    payment_method: str,
) -> dict:
    # 1. Resolve address from the user's saved addresses
    user = await db.users.find_one({"_id": _to_object_id(user_id, "user id")})
    if not user:
        raise NotFoundException("User not found")

    address = next((a for a in user.get("addresses", []) if a["_id"] == address_id), None)
    if not address:
        raise NotFoundException("Address not found")

    # 2. Get live cart + summary (recomputes prices, discount, tax fresh — never trust client totals)
    cart_data = await cart_service.get_cart(db, user_id)
    if not cart_data["items"]:
        raise BadRequestException("Your cart is empty")

    out_of_stock = [it["name"] for it in cart_data["items"] if not it["in_stock"]]
    if out_of_stock:
        raise BadRequestException(f"Out of stock: {', '.join(out_of_stock)}")

    summary = await cart_service.get_cart_summary(db, user_id)

    # 3. Deduct stock — best-effort sequential deduction with rollback.
    #    NOTE: wrap this in a Mongo session/transaction (db.client.start_session())
    #    if you're on a replica set — standalone Mongo can't do multi-doc transactions.
    deducted = []
    try:
        for item in cart_data["items"]:
            oid = _to_object_id(item["product_id"], "product id")
            query = {"_id": oid}
            update = {"$inc": {"stock": -item["qty"], "total_sold": item["qty"]}}
            if item.get("variant_name"):
                query["variants.name"] = item["variant_name"]
                update = {
                    "$inc": {"variants.$.stock": -item["qty"], "total_sold": item["qty"]}
                }
            query["stock" if not item.get("variant_name") else "variants.stock"] = {"$gte": item["qty"]}

            result = await db.products.update_one(query, update)
            if result.modified_count == 0:
                raise BadRequestException(f"'{item['name']}' just went out of stock. Please update your cart.")
            deducted.append(item)
    except Exception:
        # rollback whatever we already deducted
        for item in deducted:
            oid = ObjectId(item["product_id"])
            if item.get("variant_name"):
                await db.products.update_one(
                    {"_id": oid, "variants.name": item["variant_name"]},
                    {"$inc": {"variants.$.stock": item["qty"], "total_sold": -item["qty"]}},
                )
            else:
                await db.products.update_one(
                    {"_id": oid},
                    {"$inc": {"stock": item["qty"], "total_sold": -item["qty"]}},
                )
        raise

    # 4. Bump coupon usage count + record who used it (for admin usage audit)
    if summary.get("applied_coupon"):
        await db.coupons.update_one(
            {"code": summary["applied_coupon"]},
            {"$inc": {"used_count": 1}},
        )
        await db.coupon_usage.insert_one({
            "coupon_code": summary["applied_coupon"],
            "user_id": user_id,
            "order_id": str(result.inserted_id),
            "discount_amount": summary["discount"],
            "order_total": summary["total"],
            "used_at": datetime.utcnow(),
        })

    # 5. Build order document
    now = datetime.utcnow()
    order_doc = {
        "order_number": _generate_order_number(),
        "user_id": user_id,
        "items": [
            {
                "product_id": it["product_id"],
                "variant_name": it.get("variant_name"),
                "name": it["name"],
                "image": it.get("image"),
                "price": it["price"],
                "qty": it["qty"],
                "line_total": it["line_total"],
            }
            for it in cart_data["items"]
        ],
        "address": {
            "full_name": address["full_name"],
            "phone": address["phone"],
            "address_line1": address["address_line1"],
            "address_line2": address.get("address_line2"),
            "city": address["city"],
            "state": address["state"],
            "postal_code": address["postal_code"],
            "landmark": address.get("landmark"),
        },
        "subtotal": summary["subtotal"],
        "discount": summary["discount"],
        "tax": summary["tax"],
        "delivery_fee": summary["delivery_fee"],
        "total": summary["total"],
        "coupon_code": summary.get("applied_coupon"),
        "status": "pending",
        "payment_method": payment_method,
        "payment_status": "pending" if payment_method == "cod" else "pending",  # update once gateway added
        "status_history": [{"status": "pending", "timestamp": now, "note": "Order placed"}],
        "estimated_delivery": now + timedelta(hours=DELIVERY_ESTIMATE_HOURS),
        "created_at": now,
        "updated_at": now,
    }

    result = await db.orders.insert_one(order_doc)

    # 6. Clear the cart now that the order is placed
    await cart_service.clear_cart(db, user_id)

    order_doc["_id"] = result.inserted_id
    return _out(order_doc)


# ── LIST ORDERS ───────────────────────────────────────────────
async def list_orders(db, user_id: str, page: int = 1, limit: int = 10) -> dict:
    page = max(page, 1)
    limit = min(max(limit, 1), 50)
    skip = (page - 1) * limit

    query = {"user_id": user_id}
    total = await db.orders.count_documents(query)
    cursor = db.orders.find(query).sort([("created_at", -1)]).skip(skip).limit(limit)
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


# ── ACTIVE ORDERS ────────────────────────────────────────────
async def list_active_orders(db, user_id: str) -> list:
    cursor = db.orders.find(
        {"user_id": user_id, "status": {"$in": ACTIVE_STATUSES}}
    ).sort([("created_at", -1)])
    return [_out(doc) async for doc in cursor]


# ── GET SINGLE ORDER (ownership enforced) ─────────────────────
async def get_order(db, user_id: str, order_id: str) -> dict:
    order = await db.orders.find_one({
        "_id": _to_object_id(order_id, "order id"),
        "user_id": user_id,   # critical: prevents viewing other users' orders by guessing IDs
    })
    if not order:
        raise NotFoundException("Order not found")
    return _out(order)


# ── TRACKING ──────────────────────────────────────────────────
async def track_order(db, user_id: str, order_id: str) -> dict:
    order = await get_order(db, user_id, order_id)
    return {
        "order_number": order["order_number"],
        "status": order["status"],
        "status_history": order["status_history"],
        "estimated_delivery": order.get("estimated_delivery"),
    }


# ── CANCEL ORDER ──────────────────────────────────────────────
async def cancel_order(db, user_id: str, order_id: str, reason: Optional[str] = None) -> dict:
    order_oid = _to_object_id(order_id, "order id")
    order = await db.orders.find_one({"_id": order_oid, "user_id": user_id})
    if not order:
        raise NotFoundException("Order not found")

    if order["status"] not in CANCELLABLE_STATUSES:
        raise BadRequestException(
            f"Order cannot be cancelled once it is '{order['status']}'"
        )

    # restock items
    for item in order["items"]:
        oid = ObjectId(item["product_id"])
        if item.get("variant_name"):
            await db.products.update_one(
                {"_id": oid, "variants.name": item["variant_name"]},
                {"$inc": {"variants.$.stock": item["qty"], "total_sold": -item["qty"]}},
            )
        else:
            await db.products.update_one(
                {"_id": oid},
                {"$inc": {"stock": item["qty"], "total_sold": -item["qty"]}},
            )

    now = datetime.utcnow()
    await db.orders.update_one(
        {"_id": order_oid},
        {
            "$set": {"status": "cancelled", "updated_at": now},
            "$push": {"status_history": {
                "status": "cancelled",
                "timestamp": now,
                "note": reason or "Cancelled by customer",
            }},
        },
    )
    return await get_order(db, user_id, order_id)


# ── REORDER ───────────────────────────────────────────────────
async def reorder(db, user_id: str, order_id: str) -> dict:
    order = await get_order(db, user_id, order_id)

    added, skipped = [], []
    for item in order["items"]:
        try:
            await cart_service.add_item(
                db=db,
                user_id=user_id,
                product_id=item["product_id"],
                variant_name=item.get("variant_name"),
                qty=item["qty"],
            )
            added.append(item["name"])
        except Exception:
            # product deleted, deactivated, or out of stock — skip it, don't fail the whole reorder
            skipped.append(item["name"])

    return {"added": added, "skipped": skipped}