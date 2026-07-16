# GET    /admin/customers                 All customers with order count + total spend
# GET    /admin/customers/:id             Customer profile + full order history
# PUT    /admin/customers/:id/block       Block/unblock a customer account
# POST   /admin/customers/:id/reward      Manually add/deduct reward points

from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.common import SuccessResponse
from app.schemas.admin_customer import (
    BlockCustomerRequest,
    AdjustRewardRequest,
    CustomerListResponse,
    CustomerDetailResponse,
    BlockCustomerResponse,
    RewardAdjustResponse,
)
from app.services import admin_customer_service
from app.utils.helpers import success_response

router = APIRouter(dependencies=[Depends(get_current_admin)])


@router.get("", response_model=SuccessResponse[CustomerListResponse])
async def list_customers(
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    result = await admin_customer_service.list_customers(db=db, search=search, page=page, limit=limit)
    return success_response(data=result)


@router.get("/{customer_id}", response_model=SuccessResponse[CustomerDetailResponse])
async def get_customer(customer_id: str, db=Depends(get_db)):
    result = await admin_customer_service.get_customer(db=db, customer_id=customer_id)
    return success_response(data=result)


@router.put("/{customer_id}/block", response_model=SuccessResponse[BlockCustomerResponse])
async def toggle_block(
    customer_id: str,
    body: BlockCustomerRequest,
    db=Depends(get_db),
):
    result = await admin_customer_service.toggle_block(db=db, customer_id=customer_id, reason=body.reason)
    return success_response(data=result)


@router.post("/{customer_id}/reward", response_model=SuccessResponse[RewardAdjustResponse])
async def adjust_reward(
    customer_id: str,
    body: AdjustRewardRequest,
    current_admin=Depends(get_current_admin),
    db=Depends(get_db),
):
    result = await admin_customer_service.adjust_reward(
        db=db, customer_id=customer_id, admin_id=current_admin["_id"],
        points=body.points, reason=body.reason,
    )
    return success_response(data=result, message="Reward points adjusted")