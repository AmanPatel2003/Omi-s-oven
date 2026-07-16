from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CartItem(BaseModel):
    product_id: str
    variant_name: Optional[str] = None   # e.g. "1kg", "Half kg" — None if product has no variants
    qty: int


class CartModel(BaseModel):
    user_id: str
    items: list[CartItem] = Field(default_factory=list)
    applied_coupon: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CouponModel(BaseModel):
    code: str
    discount_type: str          # "percentage" | "flat"
    discount_value: float
    max_discount: Optional[float] = None   # cap for percentage coupons
    min_order_value: float = 0
    usage_limit: Optional[int] = None
    used_count: int = 0
    expires_at: Optional[datetime] = None
    is_active: bool = True