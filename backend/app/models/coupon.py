from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CouponModel(BaseModel):
    code: str
    description: Optional[str] = None       # customer-facing text, e.g. "20% off, up to ₹200"
    discount_type: str                       # "percentage" | "flat"
    discount_value: float
    max_discount: Optional[float] = None
    min_order_value: float = 0
    usage_limit: Optional[int] = None
    used_count: int = 0
    is_public: bool = True                   # False = hidden/targeted codes, valid but not listed
    expires_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime