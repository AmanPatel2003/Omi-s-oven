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
    doc["subcategory_count"] = await db.categories.count_documents({
        "parent_id": doc["id"]
    })

    doc["parent_name"] = None
    if doc.get("parent_id"):
        parent = await db.categories.find_one({"_id": _to_object_id(doc["parent_id"])})
        doc["parent_name"] = parent["name"] if parent else None

    return doc

async def _validate_parent(db, parent_id: str | None):
    if not parent_id:
        return
    oid = _to_object_id(parent_id, "parent_id")
    parent = await db.categories.find_one({"_id": oid})
    if not parent:
        raise BadRequestException("Parent category not found")
    if parent.get("parent_id"):
        raise BadRequestException(
            "Cannot nest a subcategory under another subcategory — only one level of nesting is allowed"
        )

# ── LIST ALL (incl. inactive) ────────────────────────────────────────
async def list_all_categories(db) -> list:
    cursor = db.categories.find({}).sort([("sort_order", 1), ("name", 1)])
    all_docs = await cursor.to_list(length=None)

    out = []
    for doc in all_docs:
        out.append(await _out_with_count(db, dict(doc)))

    mains = [c for c in out if not c.get("parent_id")]
    subs_by_parent = {}
    for c in out:
        if c.get("parent_id"):
            subs_by_parent.setdefault(c["parent_id"], []).append(c)

    for main in mains:
        main["subcategories"] = subs_by_parent.get(main["id"], [])

    return mains


# ── CREATE ──────────────────────────────────────────────────────────
async def create_category(db, data: dict) -> dict:
    if await db.categories.find_one({"slug": data["slug"]}):
        raise ConflictException("A category with this slug already exists")

    await _validate_parent(db, data.get("parent_id"))

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


async def update_category(db, category_id: str, data: dict) -> dict:
    oid = _to_object_id(category_id, "category id")
    category = await db.categories.find_one({"_id": oid})
    if not category:
        raise NotFoundException("Category not found")

    update_data = {k: v for k, v in data.items() if v is not None}
    if not update_data:
        raise BadRequestException("No fields to update")

    if "parent_id" in update_data:
        if update_data["parent_id"] == category_id:
            raise BadRequestException("A category cannot be its own parent")
        await _validate_parent(db, update_data["parent_id"])
        # if THIS category already has subcategories, it can't become a subcategory itself
        has_children = await db.categories.count_documents({"parent_id": category_id})
        if has_children:
            raise BadRequestException(
                "This category has subcategories under it — cannot also make it a subcategory"
            )

    old_slug = category["slug"]
    new_slug = update_data.get("slug")
    if new_slug and new_slug != old_slug:
        if await db.categories.find_one({"slug": new_slug}):
            raise ConflictException("A category with this slug already exists")

    update_data["updated_at"] = datetime.utcnow()
    await db.categories.update_one({"_id": oid}, {"$set": update_data})

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

    subcategory_count = await db.categories.count_documents({"parent_id": category_id})
    if subcategory_count > 0 and not force:
        raise BadRequestException(
            f"This category has {subcategory_count} subcategories. Delete or reassign them first, "
            f"or pass force=true to delete anyway (subcategories will become orphaned)."
        )

    product_count = await db.products.count_documents({"category": category["slug"]})
    if product_count > 0 and not force:
        await db.categories.update_one(
            {"_id": oid}, {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        updated = await db.categories.find_one({"_id": oid})
        result = await _out_with_count(db, updated)
        result["deleted"] = False
        result["deactivated"] = True
        return result

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