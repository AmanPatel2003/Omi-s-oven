# POST   /coupons/validate           Check if a code is valid for current cart
# GET    /coupons/active             List publicly available promo codes

from fastapi import APIRouter, Depends

from app.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.common import SuccessResponse
from app.schemas.coupon import ValidateCouponRequest, ValidateCouponResponse, CouponResponse
from app.services import coupon_service
from app.utils.helpers import success_response

router = APIRouter()


@router.get("/active", response_model=SuccessResponse[list[CouponResponse]])
async def list_active_coupons(db=Depends(get_db)):
    result = await coupon_service.list_active_coupons(db=db)
    return success_response(data=result)


@router.post("/validate", response_model=SuccessResponse[ValidateCouponResponse])
async def validate_coupon(
    body: ValidateCouponRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await coupon_service.validate_coupon(db=db, user_id=current_user["_id"], code=body.code)
    return success_response(data=result)