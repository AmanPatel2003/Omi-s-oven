# GET    /admin/coupons                   All coupons with usage stats
# POST   /admin/coupons                   Create new promo code
# PUT    /admin/coupons/:id               Edit coupon
# DELETE /admin/coupons/:id               Deactivate coupon
# GET    /admin/coupons/:id/usage         Who used this coupon and when

from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.common import SuccessResponse
from app.schemas.admin_coupon import (
    CreateCouponRequest,
    UpdateCouponRequest,
    AdminCouponResponse,
    CouponUsageResponse,
)
from app.services import admin_coupon_service
from app.utils.helpers import success_response

router = APIRouter(dependencies=[Depends(get_current_admin)])


@router.get("", response_model=SuccessResponse[list[AdminCouponResponse]])
async def list_coupons(db=Depends(get_db)):
    result = await admin_coupon_service.list_coupons(db=db)
    return success_response(data=result)


@router.post("", response_model=SuccessResponse[AdminCouponResponse])
async def create_coupon(body: CreateCouponRequest, db=Depends(get_db)):
    result = await admin_coupon_service.create_coupon(db=db, data=body.model_dump())
    return success_response(data=result, message="Coupon created successfully")


@router.put("/{coupon_id}", response_model=SuccessResponse[AdminCouponResponse])
async def update_coupon(coupon_id: str, body: UpdateCouponRequest, db=Depends(get_db)):
    result = await admin_coupon_service.update_coupon(
        db=db, coupon_id=coupon_id, data=body.model_dump(exclude_unset=True)
    )
    return success_response(data=result, message="Coupon updated successfully")


@router.delete("/{coupon_id}", response_model=SuccessResponse[AdminCouponResponse])
async def deactivate_coupon(coupon_id: str, db=Depends(get_db)):
    result = await admin_coupon_service.deactivate_coupon(db=db, coupon_id=coupon_id)
    return success_response(data=result, message="Coupon deactivated")


@router.get("/{coupon_id}/usage", response_model=SuccessResponse[CouponUsageResponse])
async def get_usage(
    coupon_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    result = await admin_coupon_service.get_usage(db=db, coupon_id=coupon_id, page=page, limit=limit)
    return success_response(data=result)