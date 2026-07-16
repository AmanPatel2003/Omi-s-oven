from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class CreatePaymentRequest(BaseModel):
    order_id: str    # our internal order id — amount is looked up, never trusted from client


class CreatePaymentResponse(BaseModel):
    razorpay_order_id: str
    amount: int          # in paise — Razorpay checkout.js expects paise
    currency: str
    razorpay_key_id: str  # public key, safe to expose to frontend
    order_id: str


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class RefundRequest(BaseModel):
    reason: Optional[str] = None
    amount: Optional[float] = None   # partial refund; None = full refund

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Refund amount must be greater than zero")
        return v


class PaymentResponse(BaseModel):
    id: str
    order_id: str
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    amount: float
    currency: str
    status: str
    method: Optional[str] = None
    refund_status: Optional[str] = None
    refund_amount: Optional[float] = None
    created_at: datetime