# GET    /admin/custom-orders             All custom cake requests
# GET    /admin/custom-orders/:id         Full custom order detail
# PUT    /admin/custom-orders/:id/status  Update status
# POST   /admin/custom-orders/:id/quote   Set price quote for customer

from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.common import SuccessResponse
from app.schemas.admin_custom_order import (
    UpdateCustomOrderStatusRequest,
    SetQuoteRequest,
    AdminCustomOrderListResponse,
    AdminCustomOrderDetailResponse,
)
from app.services import admin_custom_order_service
from app.utils.helpers import success_response

router = APIRouter(dependencies=[Depends(get_current_admin)])


@router.get("", response_model=SuccessResponse[AdminCustomOrderListResponse])
async def list_custom_orders(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    result = await admin_custom_order_service.list_custom_orders(db=db, status=status, page=page, limit=limit)
    return success_response(data=result)


@router.put("/{request_id}/status", response_model=SuccessResponse[AdminCustomOrderDetailResponse])
async def update_status(
    request_id: str,
    body: UpdateCustomOrderStatusRequest,
    db=Depends(get_db),
):
    result = await admin_custom_order_service.update_status(
        db=db, request_id=request_id, new_status=body.status, admin_note=body.admin_note,
    )
    return success_response(data=result, message=f"Status updated to {body.status}")


@router.post("/{request_id}/quote", response_model=SuccessResponse[AdminCustomOrderDetailResponse])
async def set_quote(
    request_id: str,
    body: SetQuoteRequest,
    db=Depends(get_db),
):
    result = await admin_custom_order_service.set_quote(
        db=db, request_id=request_id, quoted_price=body.quoted_price, admin_note=body.admin_note,
    )
    return success_response(data=result, message="Quote sent to customer")


@router.get("/{request_id}", response_model=SuccessResponse[AdminCustomOrderDetailResponse])
async def get_custom_order(request_id: str, db=Depends(get_db)):
    result = await admin_custom_order_service.get_custom_order(db=db, request_id=request_id)
    return success_response(data=result)