# GET    /admin/categories                All categories including inactive
# POST   /admin/categories                Create new category
# PUT    /admin/categories/:id            Edit category
# DELETE /admin/categories/:id            Delete category
# PUT    /admin/categories/reorder        Update sort_order for display

from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.common import SuccessResponse
from app.schemas.admin_category import (
    CreateCategoryRequest,
    UpdateCategoryRequest,
    ReorderCategoriesRequest,
    AdminCategoryResponse,
)
from app.services import admin_category_service
from app.utils.helpers import success_response

router = APIRouter(dependencies=[Depends(get_current_admin)])


# ── STATIC ROUTE FIRST — /reorder before /{category_id} ─────────────

@router.put("/reorder", response_model=SuccessResponse[list[AdminCategoryResponse]])
async def reorder_categories(body: ReorderCategoriesRequest, db=Depends(get_db)):
    result = await admin_category_service.reorder_categories(
        db=db, items=[item.model_dump() for item in body.items]
    )
    return success_response(data=result, message="Category order updated")


# ── LIST / CREATE ─────────────────────────────────────────────────────

@router.get("", response_model=SuccessResponse[list[AdminCategoryResponse]])
async def list_categories(db=Depends(get_db)):
    result = await admin_category_service.list_all_categories(db=db)
    return success_response(data=result)


@router.post("", response_model=SuccessResponse[AdminCategoryResponse])
async def create_category(body: CreateCategoryRequest, db=Depends(get_db)):
    result = await admin_category_service.create_category(db=db, data=body.model_dump())
    return success_response(data=result, message="Category created successfully")


# ── UPDATE / DELETE — dynamic {category_id} last ─────────────────────

@router.put("/{category_id}", response_model=SuccessResponse[AdminCategoryResponse])
async def update_category(category_id: str, body: UpdateCategoryRequest, db=Depends(get_db)):
    result = await admin_category_service.update_category(
        db=db, category_id=category_id, data=body.model_dump(exclude_unset=True)
    )
    return success_response(data=result, message="Category updated successfully")


@router.delete("/{category_id}")
async def delete_category(
    category_id: str,
    force: bool = Query(False, description="Hard-delete even if products reference this category"),
    db=Depends(get_db),
):
    result = await admin_category_service.delete_category(db=db, category_id=category_id, force=force)
    message = "Category permanently deleted" if result["deleted"] else "Category deactivated (has linked products)"
    return success_response(data=result, message=message)