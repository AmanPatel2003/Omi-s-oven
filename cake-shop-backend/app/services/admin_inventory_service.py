from datetime import datetime
from bson import ObjectId

from app.core.exceptions import NotFoundException, BadRequestException, ConflictException


def _to_object_id(id_str: str, label: str = "id"):
    try:
        return ObjectId(id_str)
    except Exception:
        raise BadRequestException(f"Invalid {label}")


def _out(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    doc["is_low_stock"] = doc["current_stock"] <= doc["low_stock_threshold"]
    return doc


async def _find_ingredient(db, ingredient_id: str) -> dict:
    oid = _to_object_id(ingredient_id, "ingredient id")
    ingredient = await db.ingredients.find_one({"_id": oid})
    if not ingredient:
        raise NotFoundException("Ingredient not found")
    return ingredient


async def _record_movement(db, ingredient_id: str, type: str, quantity: float, balance_after: float,
                            reason: str, performed_by: str, reference: str | None = None):
    await db.stock_movements.insert_one({
        "ingredient_id": ingredient_id,
        "type": type,
        "quantity": quantity,
        "balance_after": balance_after,
        "reason": reason,
        "reference": reference,
        "performed_by": performed_by,
        "created_at": datetime.utcnow(),
    })


# ── LIST ALL ──────────────────────────────────────────────────────
async def list_ingredients(db) -> list:
    cursor = db.ingredients.find({}).sort([("name", 1)])
    return [_out(doc) async for doc in cursor]


# ── CREATE ──────────────────────────────────────────────────────────
async def create_ingredient(db, data: dict) -> dict:
    if await db.ingredients.find_one({"name": {"$regex": f"^{data['name']}$", "$options": "i"}}):
        raise ConflictException("An ingredient with this name already exists")

    now = datetime.utcnow()
    doc = {**data, "is_active": True, "created_at": now, "updated_at": now}
    result = await db.ingredients.insert_one(doc)
    doc["_id"] = result.inserted_id

    # log the initial stock as an opening movement, so history is complete from day one
    if doc["current_stock"] > 0:
        await _record_movement(
            db, str(doc["_id"]), "restock", doc["current_stock"], doc["current_stock"],
            reason="Initial stock", performed_by="system",
        )

    return _out(doc)


# ── UPDATE DETAILS (not stock — see restock/adjust for that) ────────
async def update_ingredient(db, ingredient_id: str, data: dict) -> dict:
    ingredient = await _find_ingredient(db, ingredient_id)

    update_data = {k: v for k, v in data.items() if v is not None}
    if not update_data:
        raise BadRequestException("No fields to update")

    if "name" in update_data and update_data["name"].lower() != ingredient["name"].lower():
        existing = await db.ingredients.find_one({
            "name": {"$regex": f"^{update_data['name']}$", "$options": "i"}
        })
        if existing:
            raise ConflictException("An ingredient with this name already exists")

    update_data["updated_at"] = datetime.utcnow()
    await db.ingredients.update_one({"_id": ingredient["_id"]}, {"$set": update_data})

    updated = await db.ingredients.find_one({"_id": ingredient["_id"]})
    return _out(updated)


# ── RESTOCK (purchase entry — always adds) ───────────────────────────
async def restock(db, ingredient_id: str, quantity: float, cost_per_unit: float | None,
                   reference: str | None, reason: str, admin_id: str) -> dict:
    ingredient = await _find_ingredient(db, ingredient_id)

    new_balance = ingredient["current_stock"] + quantity
    update_fields = {"current_stock": new_balance, "updated_at": datetime.utcnow()}
    if cost_per_unit is not None:
        update_fields["cost_per_unit"] = cost_per_unit

    await db.ingredients.update_one({"_id": ingredient["_id"]}, {"$set": update_fields})
    await _record_movement(
        db, ingredient_id, "restock", quantity, new_balance,
        reason=reason, performed_by=admin_id, reference=reference,
    )

    updated = await db.ingredients.find_one({"_id": ingredient["_id"]})
    return _out(updated)


# ── MANUAL ADJUSTMENT (wastage, spoilage, recount correction) ────────
async def adjust_stock(db, ingredient_id: str, quantity: float, reason: str, admin_id: str) -> dict:
    ingredient = await _find_ingredient(db, ingredient_id)

    new_balance = ingredient["current_stock"] + quantity
    if new_balance < 0:
        raise BadRequestException(
            f"Adjustment would result in negative stock ({new_balance}). "
            f"Current stock is {ingredient['current_stock']}."
        )

    await db.ingredients.update_one(
        {"_id": ingredient["_id"]},
        {"$set": {"current_stock": new_balance, "updated_at": datetime.utcnow()}},
    )
    await _record_movement(
        db, ingredient_id, "adjustment", quantity, new_balance,
        reason=reason, performed_by=admin_id,
    )

    updated = await db.ingredients.find_one({"_id": ingredient["_id"]})
    return _out(updated)


# ── MOVEMENT HISTORY ──────────────────────────────────────────────────
async def get_movements(db, ingredient_id: str, page: int = 1, limit: int = 20) -> dict:
    await _find_ingredient(db, ingredient_id)   # 404 if ingredient doesn't exist

    page = max(page, 1)
    limit = min(max(limit, 1), 100)
    skip = (page - 1) * limit

    query = {"ingredient_id": ingredient_id}
    total = await db.stock_movements.count_documents(query)
    cursor = db.stock_movements.find(query).sort([("created_at", -1)]).skip(skip).limit(limit)

    items = []
    async for m in cursor:
        m["id"] = str(m.pop("_id"))
        if m["performed_by"] == "system":
            m["performed_by_name"] = "System"
        else:
            try:
                admin = await db.users.find_one({"_id": ObjectId(m["performed_by"])})
                m["performed_by_name"] = admin["name"] if admin else "Unknown"
            except Exception:
                m["performed_by_name"] = "Unknown"
        items.append(m)

    return {
        "items": items,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total else 0,
        },
    }


# ── LOW STOCK ALERTS ────────────────────────────────────────────────
async def get_alerts(db) -> list:
    cursor = db.ingredients.find({
        "is_active": True,
        "$expr": {"$lte": ["$current_stock", "$low_stock_threshold"]},
    }).sort([("current_stock", 1)])
    return [_out(doc) async for doc in cursor]