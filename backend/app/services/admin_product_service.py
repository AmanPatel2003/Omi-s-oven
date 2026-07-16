from datetime import datetime
from bson import ObjectId

from app.core.exceptions import NotFoundException, BadRequestException, ConflictException
from app.core.cloudinary_client import upload_image, delete_image


def _to_object_id(id_str: str, label: str = "id"):
    try:
        return ObjectId(id_str)
    except Exception:
        raise BadRequestException(f"Invalid {label}")


def _out(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


async def _find_product(db, product_id: str) -> dict:
    oid = _to_object_id(product_id, "product id")
    product = await db.products.find_one({"_id": oid})
    if not product:
        raise NotFoundException("Product not found")
    return product


# ── CREATE ────────────────────────────────────────────────────────
async def create_product(db, data: dict) -> dict:
    if await db.products.find_one({"slug": data["slug"]}):
        raise ConflictException("A product with this slug already exists")

    now = datetime.utcnow()
    doc = {
        **data,
        "images": [],
        "is_available": True,
        "is_featured": False,
        "total_sold": 0,
        "avg_rating": 0.0,
        "review_count": 0,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.products.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _out(doc)


# ── UPDATE ────────────────────────────────────────────────────────
async def update_product(db, product_id: str, data: dict) -> dict:
    product = await _find_product(db, product_id)

    update_data = {k: v for k, v in data.items() if v is not None}
    if not update_data:
        raise BadRequestException("No fields to update")

    if "slug" in update_data and update_data["slug"] != product["slug"]:
        existing = await db.products.find_one({"slug": update_data["slug"]})
        if existing:
            raise ConflictException("A product with this slug already exists")

    if "discount_price" in update_data:
        price = update_data.get("price", product["price"])
        if update_data["discount_price"] is not None and update_data["discount_price"] >= price:
            raise BadRequestException("Discount price must be less than the regular price")

    update_data["updated_at"] = datetime.utcnow()
    await db.products.update_one({"_id": product["_id"]}, {"$set": update_data})

    updated = await db.products.find_one({"_id": product["_id"]})
    return _out(updated)


# ── SOFT DELETE ───────────────────────────────────────────────────
async def delete_product(db, product_id: str) -> dict:
    product = await _find_product(db, product_id)
    await db.products.update_one(
        {"_id": product["_id"]},
        {"$set": {"is_available": False, "updated_at": datetime.utcnow()}},
    )
    updated = await db.products.find_one({"_id": product["_id"]})
    return _out(updated)


# ── TOGGLE AVAILABILITY ───────────────────────────────────────────
async def toggle_availability(db, product_id: str) -> dict:
    product = await _find_product(db, product_id)
    new_value = not product.get("is_available", True)
    await db.products.update_one(
        {"_id": product["_id"]},
        {"$set": {"is_available": new_value, "updated_at": datetime.utcnow()}},
    )
    updated = await db.products.find_one({"_id": product["_id"]})
    return _out(updated)


# ── TOGGLE FEATURED ────────────────────────────────────────────────
async def toggle_featured(db, product_id: str) -> dict:
    product = await _find_product(db, product_id)
    new_value = not product.get("is_featured", False)
    await db.products.update_one(
        {"_id": product["_id"]},
        {"$set": {"is_featured": new_value, "updated_at": datetime.utcnow()}},
    )
    updated = await db.products.find_one({"_id": product["_id"]})
    return _out(updated)


# ── UPLOAD IMAGES ─────────────────────────────────────────────────
MAX_IMAGES_PER_PRODUCT = 6

async def add_images(db, product_id: str, files: list) -> dict:
    product = await _find_product(db, product_id)

    existing_count = len(product.get("images", []))
    if existing_count + len(files) > MAX_IMAGES_PER_PRODUCT:
        raise BadRequestException(f"A product can have at most {MAX_IMAGES_PER_PRODUCT} images")

    uploaded = []
    try:
        for file in files:
            result = await upload_image(file, folder=f"products/{product['slug']}")
            uploaded.append(result)
    except Exception:
        # rollback any images that succeeded before the failure
        for img in uploaded:
            delete_image(img["public_id"])
        raise

    await db.products.update_one(
        {"_id": product["_id"]},
        {"$push": {"images": {"$each": uploaded}}, "$set": {"updated_at": datetime.utcnow()}},
    )

    updated = await db.products.find_one({"_id": product["_id"]})
    return _out(updated)


# ── DELETE IMAGE ──────────────────────────────────────────────────
async def remove_image(db, product_id: str, public_id: str) -> dict:
    product = await _find_product(db, product_id)

    image = next((img for img in product.get("images", []) if img["public_id"] == public_id), None)
    if not image:
        raise NotFoundException("Image not found on this product")

    delete_image(public_id)   # best-effort — proceed with DB removal even if Cloudinary delete fails

    await db.products.update_one(
        {"_id": product["_id"]},
        {"$pull": {"images": {"public_id": public_id}}, "$set": {"updated_at": datetime.utcnow()}},
    )

    updated = await db.products.find_one({"_id": product["_id"]})
    return _out(updated)


# ── UPDATE STOCK ──────────────────────────────────────────────────
async def update_stock(db, product_id: str, variant_name: str | None, stock: int) -> dict:
    product = await _find_product(db, product_id)

    if variant_name:
        variants = product.get("variants", [])
        idx = next((i for i, v in enumerate(variants) if v["name"] == variant_name), None)
        if idx is None:
            raise NotFoundException(f"Variant '{variant_name}' not found on this product")
        variants[idx]["stock"] = stock
        await db.products.update_one(
            {"_id": product["_id"]},
            {"$set": {"variants": variants, "updated_at": datetime.utcnow()}},
        )
    else:
        if product.get("variants"):
            raise BadRequestException(
                "This product uses variants — specify variant_name to update its stock"
            )
        await db.products.update_one(
            {"_id": product["_id"]},
            {"$set": {"stock": stock, "updated_at": datetime.utcnow()}},
        )

    updated = await db.products.find_one({"_id": product["_id"]})
    return _out(updated)