# POST   /custom-orders              Submit a custom cake request
# GET    /custom-orders              My custom order requests
# GET    /custom-orders/:id          Single custom order detail + status

from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.common import SuccessResponse
from app.schemas.custom_order import (
    SubmitCustomOrderRequest,
    CustomOrderDetailResponse,
    CustomOrderListResponse,
)
from app.services import custom_order_service
from app.utils.helpers import success_response

router = APIRouter()


@router.post("", response_model=SuccessResponse[CustomOrderDetailResponse])
async def submit_custom_order(
    body: SubmitCustomOrderRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await custom_order_service.submit_custom_order(
        db=db, user_id=current_user["_id"], data=body.model_dump()
    )
    return success_response(data=result, message="Custom order request submitted")


@router.get("", response_model=SuccessResponse[CustomOrderListResponse])
async def list_custom_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await custom_order_service.list_custom_orders(
        db=db, user_id=current_user["_id"], page=page, limit=limit
    )
    return success_response(data=result)


@router.get("/{request_id}", response_model=SuccessResponse[CustomOrderDetailResponse])
async def get_custom_order(
    request_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await custom_order_service.get_custom_order(
        db=db, user_id=current_user["_id"], request_id=request_id
    )
    return success_response(data=result)

@router.post("/{request_id}/accept-quote", response_model=SuccessResponse[CustomOrderDetailResponse])
async def accept_quote(
    request_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await custom_order_service.accept_quote(db=db, user_id=current_user["_id"], request_id=request_id)
    return success_response(data=result, message="Quote accepted")