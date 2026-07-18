from app.core.exceptions import NotFoundException
from app.services import product_service


def _out(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


# ── LIST CATEGORIES ──────────────────────────────────────────
async def list_categories(db) -> list:
    """Public listing — main categories with their subcategories nested, active only."""
    cursor = db.categories.find({"is_active": True}).sort([("sort_order", 1), ("name", 1)])
    all_docs = await cursor.to_list(length=None)

    def _out(doc):
        doc["id"] = str(doc.pop("_id"))
        return doc

    docs = [_out(dict(d)) for d in all_docs]
    mains = [d for d in docs if not d.get("parent_id")]
    subs_by_parent = {}
    for d in docs:
        if d.get("parent_id"):
            subs_by_parent.setdefault(d["parent_id"], []).append(d)

    for main in mains:
        main["subcategories"] = subs_by_parent.get(main["id"], [])

    return mains


async def get_category_with_products(db, slug: str, sort: str = "newest", page: int = 1, limit: int = 12) -> dict:
    category = await db.categories.find_one({"slug": slug, "is_active": True})
    if not category:
        raise NotFoundException("Category not found")

    category_id = str(category["_id"])

    if category.get("parent_id"):
        # this IS a subcategory (e.g. "wedding-cake") — only show its own products
        category_slugs = [slug]
    else:
        # this is a MAIN category — include its own slug plus every active subcategory's slug
        sub_cursor = db.categories.find({"parent_id": category_id, "is_active": True})
        subs = await sub_cursor.to_list(length=None)
        category_slugs = [slug] + [s["slug"] for s in subs]

    products = await product_service.list_products(
        db=db,
        category=None,  # can't use the existing single-category filter — see product_service change below
        category_in=category_slugs,
        sort=sort, page=page, limit=limit,
    )

    category["id"] = str(category.pop("_id"))
    return {"category": category, "products": products}