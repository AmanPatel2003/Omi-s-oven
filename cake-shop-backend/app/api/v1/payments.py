# POST   /payments/create            Create Razorpay order
# POST   /payments/verify            Verify payment signature
# POST   /payments/webhook           Razorpay webhook
# GET    /payments/:id               Get payment details for an order (order_id, per your service)
# POST   /payments/:id/refund        Request refund

from fastapi import APIRouter, Depends, Request

from app.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.common import SuccessResponse
from app.schemas.payment import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    VerifyPaymentRequest,
    RefundRequest,
    PaymentResponse,
)
from app.services import payment_service
from app.utils.helpers import success_response
from app.core.exceptions import BadRequestException

router = APIRouter()


@router.post("/create", response_model=SuccessResponse[CreatePaymentResponse])
async def create_payment(
    body: CreatePaymentRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await payment_service.create_payment(db=db, user_id=current_user["_id"], order_id=body.order_id)
    return success_response(data=result)


@router.post("/verify")
async def verify_payment(
    body: VerifyPaymentRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await payment_service.verify_payment(
        db=db,
        user_id=current_user["_id"],
        razorpay_order_id=body.razorpay_order_id,
        razorpay_payment_id=body.razorpay_payment_id,
        razorpay_signature=body.razorpay_signature,
    )
    return success_response(data=result, message="Payment verified")


@router.post("/webhook")
async def razorpay_webhook(request: Request, db=Depends(get_db)):
    """
    Razorpay calls this directly — no auth dependency, no current_user.
    Security comes entirely from the HMAC signature check inside the service.
    """
    raw_body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")
    if not signature:
        raise BadRequestException("Missing webhook signature header")

    result = await payment_service.handle_webhook(db=db, raw_body=raw_body, signature=signature)
    # Razorpay just needs a 200 — no envelope needed, but keeping it consistent is fine too
    return {"status": "ok", **result}


@router.get("/{order_id}", response_model=SuccessResponse[PaymentResponse])
async def get_payment(
    order_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await payment_service.get_payment(db=db, user_id=current_user["_id"], order_id=order_id)
    return success_response(data=result)


@router.post("/{order_id}/refund", response_model=SuccessResponse[PaymentResponse])
async def refund_payment(
    order_id: str,
    body: RefundRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await payment_service.request_refund(
        db=db,
        requesting_user=current_user,
        order_id=order_id,
        amount=body.amount,
        reason=body.reason,
    )
    return success_response(data=result, message="Refund processed successfully")