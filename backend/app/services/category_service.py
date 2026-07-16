from app.core.exceptions import NotFoundException
from app.services import product_service


def _out(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


# ── LIST CATEGORIES ──────────────────────────────────────────
async def list_categories(db) -> list:
    cursor = db.categories.find({"is_available": True}).sort([("display_order", 1), ("name", 1)])
    return [_out(doc) async for doc in cursor]


# ── CATEGORY + PRODUCTS ──────────────────────────────────────
async def get_category_with_products(
    db,
    slug: str,
    sort: str = "newest",
    page: int = 1,
    limit: int = 12,
) -> dict:
    category = await db.categories.find_one({"slug": slug, "is_available": True})
    if not category:
        raise NotFoundException("Category not found")

    products = await product_service.list_products(
        db=db,
        category=slug,
        sort=sort,
        page=page,
        limit=limit,
    )

    return {
        "category": _out(category),
        "products": products,
    }