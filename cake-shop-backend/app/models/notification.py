from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class NotificationModel(BaseModel):
    user_id: str
    type: str              # "order_placed" | "order_confirmed" | "out_for_delivery" | "delivered" |
                            # "payment_failed" | "custom_order_quoted" | "points_earned" | "promo" | etc.
    title: str
    message: str
    reference_id: Optional[str] = None   # order_id / custom_order_id / payment_id, for deep-linking
    is_read: bool = False
    created_at: datetime