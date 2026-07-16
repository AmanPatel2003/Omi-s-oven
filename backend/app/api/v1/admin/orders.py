# GET    /admin/orders                      All orders (filter by status, date, search)
# GET    /admin/orders/:id                  Full order detail
# PUT    /admin/orders/:id/status           Update order status
# POST   /admin/orders/:id/assign-delivery  Assign delivery person to order
# GET    /admin/orders/export               Export orders CSV for date range

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.database import get_db
from app.core.dependencies import get_current_admin
from app.core.exceptions import BadRequestException
from app.schemas.common import SuccessResponse
from app.schemas.admin_order import (
    UpdateOrderStatusRequest,
    AssignDeliveryRequest,
    AdminOrderListResponse,
    AdminOrderDetailResponse,
)
from app.services import admin_order_service
from app.utils.helpers import success_response

router = APIRouter(dependencies=[Depends(get_current_admin)])


# ── STATIC ROUTE FIRST — /export before /{order_id} ─────────────────

@router.get("/export")
async def export_orders(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db=Depends(get_db),
):
    # default to current month if no range given
    if not date_from:
        now = datetime.utcnow()
        date_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if not date_to:
        date_to = datetime.utcnow()
    if date_from > date_to:
        raise BadRequestException("date_from must be before date_to")

    buffer = await admin_order_service.export_orders_csv(db=db, date_from=date_from, date_to=date_to)
    filename = f"orders_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.csv"

    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── LIST ──────────────────────────────────────────────────────────────

@router.get("", response_model=SuccessResponse[AdminOrderListResponse])
async def list_orders(
    status: Optional[str] = None,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    result = await admin_order_service.list_orders(
        db=db, status=status, date_from=date_from, date_to=date_to, search=search, page=page, limit=limit,
    )
    return success_response(data=result)


# ── STATUS / ASSIGN — sub-routes on /{order_id} ─────────────────────

@router.put("/{order_id}/status", response_model=SuccessResponse[AdminOrderDetailResponse])
async def update_status(
    order_id: str,
    body: UpdateOrderStatusRequest,
    db=Depends(get_db),
):
    result = await admin_order_service.update_status(db=db, order_id=order_id, new_status=body.status, note=body.note)
    return success_response(data=result, message=f"Order status updated to {body.status}")


@router.post("/{order_id}/assign-delivery", response_model=SuccessResponse[AdminOrderDetailResponse])
async def assign_delivery(
    order_id: str,
    body: AssignDeliveryRequest,
    db=Depends(get_db),
):
    result = await admin_order_service.assign_delivery(db=db, order_id=order_id, rider_id=body.rider_id)
    return success_response(data=result, message="Delivery rider assigned")


# ── DETAIL — must be LAST, catch-all string param ────────────────────

@router.get("/{order_id}", response_model=SuccessResponse[AdminOrderDetailResponse])
async def get_order(order_id: str, db=Depends(get_db)):
    result = await admin_order_service.get_order(db=db, order_id=order_id)
    return success_response(data=result)