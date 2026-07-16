# GET    /admin/inventory                 All ingredients with stock levels
# POST   /admin/inventory                 Add new ingredient
# PUT    /admin/inventory/:id             Update ingredient details
# POST   /admin/inventory/:id/restock     Add stock (purchase entry)
# POST   /admin/inventory/:id/adjust      Manual adjustment with reason
# GET    /admin/inventory/:id/movements   Full stock movement history
# GET    /admin/inventory/alerts          All ingredients below threshold

from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.common import SuccessResponse
from app.schemas.admin_inventory import (
    CreateIngredientRequest,
    UpdateIngredientRequest,
    RestockRequest,
    AdjustStockRequest,
    IngredientResponse,
    MovementListResponse,
)
from app.services import admin_inventory_service
from app.utils.helpers import success_response

router = APIRouter(dependencies=[Depends(get_current_admin)])


# ── STATIC ROUTE FIRST — /alerts before /{ingredient_id} ─────────────

@router.get("/alerts", response_model=SuccessResponse[list[IngredientResponse]])
async def get_alerts(db=Depends(get_db)):
    result = await admin_inventory_service.get_alerts(db=db)
    return success_response(data=result)


# ── LIST / CREATE ─────────────────────────────────────────────────────

@router.get("", response_model=SuccessResponse[list[IngredientResponse]])
async def list_ingredients(db=Depends(get_db)):
    result = await admin_inventory_service.list_ingredients(db=db)
    return success_response(data=result)


@router.post("", response_model=SuccessResponse[IngredientResponse])
async def create_ingredient(body: CreateIngredientRequest, db=Depends(get_db)):
    result = await admin_inventory_service.create_ingredient(db=db, data=body.model_dump())
    return success_response(data=result, message="Ingredient added successfully")


# ── SUB-ROUTES on /{ingredient_id} ────────────────────────────────────

@router.put("/{ingredient_id}", response_model=SuccessResponse[IngredientResponse])
async def update_ingredient(ingredient_id: str, body: UpdateIngredientRequest, db=Depends(get_db)):
    result = await admin_inventory_service.update_ingredient(
        db=db, ingredient_id=ingredient_id, data=body.model_dump(exclude_unset=True)
    )
    return success_response(data=result, message="Ingredient updated")


@router.post("/{ingredient_id}/restock", response_model=SuccessResponse[IngredientResponse])
async def restock(
    ingredient_id: str,
    body: RestockRequest,
    current_admin=Depends(get_current_admin),
    db=Depends(get_db),
):
    result = await admin_inventory_service.restock(
        db=db,
        ingredient_id=ingredient_id,
        quantity=body.quantity,
        cost_per_unit=body.cost_per_unit,
        reference=body.reference,
        reason=body.reason,
        admin_id=current_admin["_id"],
    )
    return success_response(data=result, message="Stock added successfully")


@router.post("/{ingredient_id}/adjust", response_model=SuccessResponse[IngredientResponse])
async def adjust_stock(
    ingredient_id: str,
    body: AdjustStockRequest,
    current_admin=Depends(get_current_admin),
    db=Depends(get_db),
):
    result = await admin_inventory_service.adjust_stock(
        db=db,
        ingredient_id=ingredient_id,
        quantity=body.quantity,
        reason=body.reason,
        admin_id=current_admin["_id"],
    )
    return success_response(data=result, message="Stock adjusted")


@router.get("/{ingredient_id}/movements", response_model=SuccessResponse[MovementListResponse])
async def get_movements(
    ingredient_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    result = await admin_inventory_service.get_movements(db=db, ingredient_id=ingredient_id, page=page, limit=limit)
    return success_response(data=result)