# GET    /delivery/track/:order_id   Customer: live delivery location + ETA
# POST   /delivery/update-location   Delivery staff: push GPS coordinates
# POST   /delivery/confirm/:order_id Delivery staff: confirm delivery with OTP

from fastapi import APIRouter, Depends

from app.database import get_db
from app.core.dependencies import get_current_user, get_current_delivery_staff
from app.schemas.common import SuccessResponse
from app.schemas.delivery import (
    UpdateLocationRequest,
    ConfirmDeliveryRequest,
    TrackDeliveryResponse,
)
from app.services import delivery_service
from app.utils.helpers import success_response

router = APIRouter()


@router.get("/track/{order_id}", response_model=SuccessResponse[TrackDeliveryResponse])
async def track_delivery(
    order_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await delivery_service.track_delivery(db=db, user_id=current_user["_id"], order_id=order_id)
    return success_response(data=result)


@router.post("/update-location")
async def update_location(
    body: UpdateLocationRequest,
    current_rider=Depends(get_current_delivery_staff),
    db=Depends(get_db),
):
    result = await delivery_service.update_location(
        db=db,
        rider_id=current_rider["_id"],
        order_id=body.order_id,
        lat=body.lat,
        lng=body.lng,
    )
    return success_response(data=result)


@router.post("/confirm/{order_id}")
async def confirm_delivery(
    order_id: str,
    body: ConfirmDeliveryRequest,
    current_rider=Depends(get_current_delivery_staff),
    db=Depends(get_db),
):
    result = await delivery_service.confirm_delivery(
        db=db, rider_id=current_rider["_id"], order_id=order_id, otp=body.otp
    )
    return success_response(data=result, message="Delivery confirmed")