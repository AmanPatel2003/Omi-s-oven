from datetime import datetime
from typing import Optional
from bson import ObjectId

from app.core.exceptions import NotFoundException, BadRequestException
from app.utils.helpers import serialize_doc


def _to_object_id(id_str: str):
    try:
        return ObjectId(id_str)
    except Exception:
        raise BadRequestException("Invalid product id")


def _out(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


SORT_MAP = {
    "price_asc": [("price", 1)],
    "price_desc": [("price", -1)],
    "newest": [("created_at", -1)],
    "bestselling": [("total_sold", -1)],
    "rating": [("avg_rating", -1)],
}


# ── LIST PRODUCTS ────────────────────────────────────────────
async def list_products(
    db,
    category: Optional[str] = None,
    category_in: Optional[list[str]] = None,   # ← NEW
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    tag: Optional[str] = None,
    is_eggless: Optional[bool] = None,
    sort: str = "newest",
    page: int = 1,
    limit: int = 12,
) -> dict:
    query: dict = {"is_available": True}

    if category_in:
        query["category"] = {"$in": category_in}
    elif category:
        query["category"] = category
    if tag:
        query["tags"] = tag
    if is_eggless is not None:
        query["is_eggless"] = is_eggless
    if min_price is not None or max_price is not None:
        price_filter = {}
        if min_price is not None:
            price_filter["$gte"] = min_price
        if max_price is not None:
            price_filter["$lte"] = max_price
        query["price"] = price_filter
    if search:
        # regex fallback — swap for $text search once a text index exists
        # on name/description for better performance & relevance
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    page = max(page, 1)
    limit = min(max(limit, 1), 100)  # cap to avoid abuse
    skip = (page - 1) * limit

    sort_spec = SORT_MAP.get(sort, SORT_MAP["newest"])

    total = await db.products.count_documents(query)
    cursor = db.products.find(query).sort(sort_spec).skip(skip).limit(limit)
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


# ── SINGLE PRODUCT ───────────────────────────────────────────
async def get_product_by_slug(db, slug: str) -> dict:
    product = await db.products.find_one({"slug": slug, "is_available": True})
    if not product:
        raise NotFoundException("Product not found")
    return _out(product)


# ── FEATURED / BESTSELLERS / NEW ARRIVALS ────────────────────
async def get_featured_products(db, limit: int = 10) -> list:
    cursor = db.products.find(
        {"is_available": True, "is_featured": True}
    ).sort([("created_at", -1)]).limit(limit)
    return [_out(doc) async for doc in cursor]


async def get_bestsellers(db, limit: int = 10) -> list:
    cursor = db.products.find(
        {"is_available": True}
    ).sort([("total_sold", -1)]).limit(limit)
    return [_out(doc) async for doc in cursor]


async def get_new_arrivals(db, limit: int = 10) -> list:
    cursor = db.products.find(
        {"is_available": True}
    ).sort([("created_at", -1)]).limit(limit)
    return [_out(doc) async for doc in cursor]


# ── REVIEWS ───────────────────────────────────────────────────
async def add_review(
    db,
    product_id: str,
    user_id: str,
    user_name: str,
    rating: int,
    comment: Optional[str],
) -> dict:
    oid = _to_object_id(product_id)
    product = await db.products.find_one({"_id": oid, "is_available": True})
    if not product:
        raise NotFoundException("Product not found")

    # one review per user per product
    existing = await db.reviews.find_one({"product_id": product_id, "user_id": user_id})
    if existing:
        raise BadRequestException("You have already reviewed this product")

    review_doc = {
        "product_id": product_id,
        "user_id": user_id,
        "user_name": user_name,
        "rating": rating,
        "comment": comment,
        "created_at": datetime.utcnow(),
    }
    result = await db.reviews.insert_one(review_doc)

    # recompute avg_rating + review_count on the product
    new_count = product.get("review_count", 0) + 1
    new_avg = ((product.get("avg_rating", 0) * product.get("review_count", 0)) + rating) / new_count

    await db.products.update_one(
        {"_id": oid},
        {"$set": {
            "avg_rating": round(new_avg, 2),
            "review_count": new_count,
            "updated_at": datetime.utcnow(),
        }},
    )

    review_doc["id"] = str(result.inserted_id)
    return review_doc


async def list_reviews(db, product_id: str, page: int = 1, limit: int = 10) -> dict:
    _to_object_id(product_id)  # validate format even though we query by string field

    page = max(page, 1)
    limit = min(max(limit, 1), 50)
    skip = (page - 1) * limit

    query = {"product_id": product_id}
    total = await db.reviews.count_documents(query)
    cursor = db.reviews.find(query).sort([("created_at", -1)]).skip(skip).limit(limit)

    items = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        items.append(doc)

    return {
        "items": items,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total else 0,
        },
    }