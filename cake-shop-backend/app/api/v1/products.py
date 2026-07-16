'''GET/products                   List all products (paginated)
         ?category=cakes           Filter by category slug
         ?search=chocolate         Full-text search
         ?min_price=100            Price range filter
         ?max_price=2000
         ?tag=bestseller           Filter by tag
         ?sort=price_asc           Sort options
         ?is_eggless=true          Dietary filter
         ?page=1&limit=12

GET    /products/:slug             Get single product detail
GET    /products/featured          Get featured/homepage products
GET    /products/bestsellers       Top 10 by total_sold
GET    /products/new-arrivals      Latest 10 products

POST   /products/:id/reviews       Submit a product review + rating
GET    /products/:id/reviews       List reviews for a product'''


# GET    /products                   List all products (paginated)
# GET    /products/featured          Get featured/homepage products
# GET    /products/bestsellers       Top 10 by total_sold
# GET    /products/new-arrivals      Latest 10 products
# GET    /products/:slug             Get single product detail
# POST   /products/:id/reviews       Submit a product review + rating
# GET    /products/:id/reviews       List reviews for a product

from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.common import SuccessResponse
from app.schemas.product import (
    ProductListResponse,
    ProductDetailResponse,
    ProductResponse,
    ReviewRequest,
    ReviewListResponse,
    SortOption,
)
from app.services import product_service
from app.utils.helpers import success_response

router = APIRouter()


# ── STATIC ROUTES FIRST — must come before /{slug} ────────────

@router.get("/featured", response_model=SuccessResponse[list[ProductResponse]])
async def featured_products(db=Depends(get_db)):
    result = await product_service.get_featured_products(db=db, limit=10)
    return success_response(data=result)


@router.get("/bestsellers", response_model=SuccessResponse[list[ProductResponse]])
async def bestseller_products(db=Depends(get_db)):
    result = await product_service.get_bestsellers(db=db, limit=10)
    return success_response(data=result)


@router.get("/new-arrivals", response_model=SuccessResponse[list[ProductResponse]])
async def new_arrival_products(db=Depends(get_db)):
    result = await product_service.get_new_arrivals(db=db, limit=10)
    return success_response(data=result)


# ── LIST ────────────────────────────────────────────────────

@router.get("", response_model=SuccessResponse[ProductListResponse])
async def list_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    tag: Optional[str] = None,
    is_eggless: Optional[bool] = None,
    sort: SortOption = SortOption.newest,
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=100),
    db=Depends(get_db),
):
    result = await product_service.list_products(
        db=db,
        category=category,
        search=search,
        min_price=min_price,
        max_price=max_price,
        tag=tag,
        is_eggless=is_eggless,
        sort=sort.value,
        page=page,
        limit=limit,
    )
    return success_response(data=result)


# ── REVIEWS (id-based — different depth from /{slug}, safe) ──

@router.post("/{product_id}/reviews")
async def submit_review(
    product_id: str,
    body: ReviewRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await product_service.add_review(
        db=db,
        product_id=product_id,
        user_id=current_user["_id"],
        user_name=current_user.get("name", "Anonymous"),
        rating=body.rating,
        comment=body.comment,
    )
    return success_response(data=result, message="Review submitted successfully")


@router.get("/{product_id}/reviews", response_model=SuccessResponse[ReviewListResponse])
async def get_reviews(
    product_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db=Depends(get_db),
):
    result = await product_service.list_reviews(db=db, product_id=product_id, page=page, limit=limit)
    return success_response(data=result)


# ── SLUG DETAIL — must be LAST since it's a catch-all string ─

@router.get("/{slug}", response_model=SuccessResponse[ProductDetailResponse])
async def get_product(slug: str, db=Depends(get_db)):
    result = await product_service.get_product_by_slug(db=db, slug=slug)
    return success_response(data=result)


