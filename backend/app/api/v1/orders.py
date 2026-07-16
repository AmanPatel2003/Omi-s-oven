# POST   /orders                     Place a new order (from cart)
# GET    /orders                     My order history (paginated)
# GET    /orders/active              My currently active orders (not delivered)
# GET    /orders/:id                 Single order detail + status
# GET    /orders/:id/track           Live tracking info for the order
# POST   /orders/:id/cancel          Cancel order (if still pending/confirmed)
# POST   /orders/:id/reorder         Add all items from a past order to cart

from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.common import SuccessResponse
from app.schemas.order import (
    PlaceOrderRequest,
    OrderResponse,
    OrderDetailResponse,
    OrderListResponse,
    OrderTrackingResponse,
    ReorderResponse,
)
from app.services import order_service
from app.utils.helpers import success_response

router = APIRouter()


# ── STATIC ROUTES FIRST — /active before /{id} ────────────────

@router.get("/active", response_model=SuccessResponse[list[OrderResponse]])
async def active_orders(current_user=Depends(get_current_user), db=Depends(get_db)):
    result = await order_service.list_active_orders(db=db, user_id=current_user["_id"])
    return success_response(data=result)


@router.post("", response_model=SuccessResponse[OrderDetailResponse])
async def place_order(
    body: PlaceOrderRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await order_service.place_order(
        db=db,
        user_id=current_user["_id"],
        address_id=body.address_id,
        payment_method=body.payment_method,
    )
    return success_response(data=result, message="Order placed successfully")


@router.get("", response_model=SuccessResponse[OrderListResponse])
async def list_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await order_service.list_orders(db=db, user_id=current_user["_id"], page=page, limit=limit)
    return success_response(data=result)


# ── SUB-ROUTES on /{order_id} — safe, extra path segment ──────

@router.get("/{order_id}/track", response_model=SuccessResponse[OrderTrackingResponse])
async def track_order(
    order_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await order_service.track_order(db=db, user_id=current_user["_id"], order_id=order_id)
    return success_response(data=result)


@router.post("/{order_id}/cancel", response_model=SuccessResponse[OrderDetailResponse])
async def cancel_order(
    order_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await order_service.cancel_order(db=db, user_id=current_user["_id"], order_id=order_id)
    return success_response(data=result, message="Order cancelled successfully")


@router.post("/{order_id}/reorder", response_model=SuccessResponse[ReorderResponse])
async def reorder(
    order_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await order_service.reorder(db=db, user_id=current_user["_id"], order_id=order_id)
    return success_response(data=result, message="Items added to cart")


# ── DETAIL — must be LAST, catch-all string param ──────────────

@router.get("/{order_id}", response_model=SuccessResponse[OrderDetailResponse])
async def get_order(
    order_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await order_service.get_order(db=db, user_id=current_user["_id"], order_id=order_id)
    return success_response(data=result)