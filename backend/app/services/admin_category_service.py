from datetime import datetime
from bson import ObjectId

from app.core.exceptions import NotFoundException, BadRequestException, ConflictException


def _to_object_id(id_str: str, label: str = "id"):
    try:
        return ObjectId(id_str)
    except Exception:
        raise BadRequestException(f"Invalid {label}")


async def _out_with_count(db, doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    doc["product_count"] = await db.products.count_documents({
        "category": doc["slug"], "is_available": True
    })
    return doc


# ── LIST ALL (incl. inactive) ────────────────────────────────────────
async def list_all_categories(db) -> list:
    cursor = db.categories.find({}).sort([("sort_order", 1), ("name", 1)])
    items = []
    async for doc in cursor:
        items.append(await _out_with_count(db, doc))
    return items


# ── CREATE ──────────────────────────────────────────────────────────
async def create_category(db, data: dict) -> dict:
    if await db.categories.find_one({"slug": data["slug"]}):
        raise ConflictException("A category with this slug already exists")

    now = datetime.utcnow()
    doc = {
        **data,
        "image": None,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.categories.insert_one(doc)
    doc["_id"] = result.inserted_id
    return await _out_with_count(db, doc)


# ── UPDATE ──────────────────────────────────────────────────────────
async def update_category(db, category_id: str, data: dict) -> dict:
    oid = _to_object_id(category_id, "category id")
    category = await db.categories.find_one({"_id": oid})
    if not category:
        raise NotFoundException("Category not found")

    update_data = {k: v for k, v in data.items() if v is not None}
    if not update_data:
        raise BadRequestException("No fields to update")

    old_slug = category["slug"]
    new_slug = update_data.get("slug")

    if new_slug and new_slug != old_slug:
        if await db.categories.find_one({"slug": new_slug}):
            raise ConflictException("A category with this slug already exists")

    update_data["updated_at"] = datetime.utcnow()
    await db.categories.update_one({"_id": oid}, {"$set": update_data})

    # if slug changed, cascade to every product referencing the old slug —
    # otherwise those products silently fall out of the category listing
    if new_slug and new_slug != old_slug:
        await db.products.update_many(
            {"category": old_slug},
            {"$set": {"category": new_slug, "updated_at": datetime.utcnow()}},
        )

    updated = await db.categories.find_one({"_id": oid})
    return await _out_with_count(db, updated)


# ── DELETE ──────────────────────────────────────────────────────────
async def delete_category(db, category_id: str, force: bool = False) -> dict:
    oid = _to_object_id(category_id, "category id")
    category = await db.categories.find_one({"_id": oid})
    if not category:
        raise NotFoundException("Category not found")

    product_count = await db.products.count_documents({"category": category["slug"]})

    if product_count > 0 and not force:
        # soft-delete: hide from storefront, keep linked products intact
        await db.categories.update_one(
            {"_id": oid},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}},
        )
        updated = await db.categories.find_one({"_id": oid})
        result = await _out_with_count(db, updated)
        result["deleted"] = False
        result["deactivated"] = True
        return result

    # no products reference this category (or force=True) — safe to hard delete
    await db.categories.delete_one({"_id": oid})
    return {"id": category_id, "deleted": True, "deactivated": False}


# ── REORDER ──────────────────────────────────────────────────────────
async def reorder_categories(db, items: list[dict]) -> list:
    for item in items:
        oid = _to_object_id(item["id"], "category id")
        result = await db.categories.update_one(
            {"_id": oid},
            {"$set": {"sort_order": item["sort_order"], "updated_at": datetime.utcnow()}},
        )
        if result.matched_count == 0:
            raise NotFoundException(f"Category {item['id']} not found")

    return await list_all_categories(db)