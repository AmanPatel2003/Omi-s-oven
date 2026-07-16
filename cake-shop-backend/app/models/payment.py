from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PaymentModel(BaseModel):
    order_id: str                    # our internal order _id (string)
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None

    amount: float                    # in rupees (stored as float; paise used only at Razorpay API boundary)
    currency: str = "INR"

    status: str = "created"          # created -> authorized -> captured -> failed | refunded
    method: Optional[str] = None     # upi, card, netbanking, etc. (from webhook payload)

    refund_id: Optional[str] = None
    refund_status: Optional[str] = None   # requested -> processed | failed
    refund_amount: Optional[float] = None
    refund_reason: Optional[str] = None

    raw_webhook_events: list = []    # audit trail of raw webhook payloads received

    created_at: datetime
    updated_at: datetime