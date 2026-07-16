from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class CreateCouponRequest(BaseModel):
    code: str
    description: Optional[str] = None
    discount_type: str                    # "percentage" | "flat"
    discount_value: float
    max_discount: Optional[float] = None
    min_order_value: float = 0
    usage_limit: Optional[int] = None
    is_public: bool = True
    expires_at: Optional[datetime] = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v):
        v = v.strip().upper()
        if len(v) < 3:
            raise ValueError("Coupon code must be at least 3 characters")
        return v

    @field_validator("discount_type")
    @classmethod
    def validate_type(cls, v):
        if v not in ("percentage", "flat"):
            raise ValueError("discount_type must be 'percentage' or 'flat'")
        return v

    @field_validator("discount_value")
    @classmethod
    def validate_value(cls, v, info):
        if v <= 0:
            raise ValueError("Discount value must be greater than zero")
        discount_type = info.data.get("discount_type")
        if discount_type == "percentage" and v > 100:
            raise ValueError("Percentage discount cannot exceed 100")
        return v

    @field_validator("usage_limit")
    @classmethod
    def validate_limit(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Usage limit must be greater than zero")
        return v


class UpdateCouponRequest(BaseModel):
    description: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    max_discount: Optional[float] = None
    min_order_value: Optional[float] = None
    usage_limit: Optional[int] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None

    @field_validator("discount_type")
    @classmethod
    def validate_type(cls, v):
        if v is not None and v not in ("percentage", "flat"):
            raise ValueError("discount_type must be 'percentage' or 'flat'")
        return v


class AdminCouponResponse(BaseModel):
    id: str
    code: str
    description: Optional[str] = None
    discount_type: str
    discount_value: float
    max_discount: Optional[float] = None
    min_order_value: float
    usage_limit: Optional[int] = None
    used_count: int
    usage_remaining: Optional[int] = None
    is_public: bool
    is_active: bool
    expires_at: Optional[datetime] = None
    is_expired: bool
    total_discount_given: float
    created_at: datetime


class CouponUsageItem(BaseModel):
    user_id: str
    user_name: str
    user_email: str
    order_id: str
    order_number: str
    discount_amount: float
    order_total: float
    used_at: datetime


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class CouponUsageResponse(BaseModel):
    coupon_code: str
    items: list[CouponUsageItem]
    meta: PaginationMeta