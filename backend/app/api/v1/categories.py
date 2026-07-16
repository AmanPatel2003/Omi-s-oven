# GET    /categories                 List all active categories
# GET    /categories/:slug           Get category + its products

from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.schemas.common import SuccessResponse
from app.schemas.category import CategoryResponse, CategoryDetailResponse
from app.schemas.product import SortOption
from app.services import category_service
from app.utils.helpers import success_response

router = APIRouter()


@router.get("", response_model=SuccessResponse[list[CategoryResponse]])
async def list_categories(db=Depends(get_db)):
    result = await category_service.list_categories(db=db)
    return success_response(data=result)


@router.get("/{slug}", response_model=SuccessResponse[CategoryDetailResponse])
async def get_category(
    slug: str,
    sort: SortOption = SortOption.newest,
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=100),
    db=Depends(get_db),
):
    result = await category_service.get_category_with_products(
        db=db, slug=slug, sort=sort.value, page=page, limit=limit
    )
    return success_response(data=result)