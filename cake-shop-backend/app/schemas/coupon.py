from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class ValidateCouponRequest(BaseModel):
    code: str

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v):
        return v.strip().upper()


class CouponResponse(BaseModel):
    code: str
    description: Optional[str] = None
    discount_type: str
    discount_value: float
    max_discount: Optional[float] = None
    min_order_value: float
    expires_at: Optional[datetime] = None


class ValidateCouponResponse(BaseModel):
    valid: bool
    code: str
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    discount_amount: Optional[float] = None    # actual ₹ amount for THIS cart
    message: str