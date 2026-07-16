from datetime import datetime
from pydantic import BaseModel


class CouponUsageModel(BaseModel):
    coupon_code: str
    user_id: str
    order_id: str
    discount_amount: float
    order_total: float
    used_at: datetime