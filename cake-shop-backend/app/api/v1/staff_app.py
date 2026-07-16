# POST   /staff/clock-in              Staff clocks in for the day
# POST   /staff/clock-out             Staff clocks out
# GET    /staff/my-attendance         View own attendance for the month
# GET    /staff/my-salary             View own salary slips
# GET    /staff/orders/assigned       Delivery staff: see assigned deliveries
# PUT    /staff/orders/:id/pickup     Mark order as picked up from shop
# PUT    /staff/orders/:id/delivered  Mark order as delivered (with OTP)
# POST   /staff/location              Push current GPS location for live tracking

from fastapi import APIRouter, Depends

from app.database import get_db
from app.core.dependencies import get_current_staff, get_current_delivery_staff
from app.schemas.common import SuccessResponse
from app.schemas.staff import (
    ClockInRequest, ClockOutRequest, PushLocationRequest, ConfirmDeliveryRequest,
    MyAttendanceResponse, MySalaryResponse, AssignedOrderItem,
)
from app.services import staff_service, delivery_service
from app.utils.helpers import success_response

router = APIRouter()


# ── ATTENDANCE / SALARY — any staff role ─────────────────────────────

@router.post("/clock-in")
async def clock_in(
    body: ClockInRequest,
    current_staff=Depends(get_current_staff),
    db=Depends(get_db),
):
    result = await staff_service.clock_in(db=db, staff_id=current_staff["_id"], note=body.note)
    return success_response(data=result, message="Clocked in")


@router.post("/clock-out")
async def clock_out(
    body: ClockOutRequest,
    current_staff=Depends(get_current_staff),
    db=Depends(get_db),
):
    result = await staff_service.clock_out(db=db, staff_id=current_staff["_id"], note=body.note)
    return success_response(data=result, message="Clocked out")


@router.get("/my-attendance", response_model=SuccessResponse[MyAttendanceResponse])
async def my_attendance(
    current_staff=Depends(get_current_staff),
    db=Depends(get_db),
):
    result = await staff_service.get_my_attendance(db=db, staff_id=current_staff["_id"])
    return success_response(data=result)


@router.get("/my-salary", response_model=SuccessResponse[MySalaryResponse])
async def my_salary(
    current_staff=Depends(get_current_staff),
    db=Depends(get_db),
):
    result = await staff_service.get_my_salary(db=db, staff_id=current_staff["_id"])
    return success_response(data=result)


# ── DELIVERY — delivery_staff only ────────────────────────────────────

@router.get("/orders/assigned", response_model=SuccessResponse[list[AssignedOrderItem]])
async def assigned_orders(
    current_rider=Depends(get_current_delivery_staff),
    db=Depends(get_db),
):
    result = await staff_service.get_assigned_orders(db=db, rider_id=current_rider["_id"])
    return success_response(data=result)


@router.put("/orders/{order_id}/pickup")
async def mark_pickup(
    order_id: str,
    current_rider=Depends(get_current_delivery_staff),
    db=Depends(get_db),
):
    result = await staff_service.mark_pickup(db=db, rider_id=current_rider["_id"], order_id=order_id)
    return success_response(data=result, message="Order marked as picked up")


@router.put("/orders/{order_id}/delivered")
async def mark_delivered(
    order_id: str,
    body: ConfirmDeliveryRequest,
    current_rider=Depends(get_current_delivery_staff),
    db=Depends(get_db),
):
    # reuses the existing delivery_service function — same OTP/ownership logic
    # built for the customer-facing delivery module, not duplicated here
    result = await delivery_service.confirm_delivery(
        db=db, rider_id=current_rider["_id"], order_id=order_id, otp=body.otp
    )
    return success_response(data=result, message="Delivery confirmed")


@router.post("/location")
async def push_location(
    body: PushLocationRequest,
    current_rider=Depends(get_current_delivery_staff),
    db=Depends(get_db),
):
    result = await delivery_service.update_location(
        db=db, rider_id=current_rider["_id"], order_id=body.order_id, lat=body.lat, lng=body.lng,
    )
    return success_response(data=result)