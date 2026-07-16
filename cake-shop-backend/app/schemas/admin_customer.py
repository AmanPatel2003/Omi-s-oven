from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class BlockCustomerRequest(BaseModel):
    reason: Optional[str] = None


class AdjustRewardRequest(BaseModel):
    points: int              # positive = add, negative = deduct
    reason: str

    @field_validator("points")
    @classmethod
    def validate_points(cls, v):
        if v == 0:
            raise ValueError("Points adjustment cannot be zero")
        return v

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v):
        if len(v.strip()) < 3:
            raise ValueError("Please provide a reason for this adjustment")
        return v.strip()


class CustomerListItem(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    is_active: bool
    order_count: int
    total_spend: float
    reward_points: int
    joined_at: datetime


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class CustomerListResponse(BaseModel):
    items: list[CustomerListItem]
    meta: PaginationMeta


class OrderSummaryItem(BaseModel):
    id: str
    order_number: str
    total: float
    status: str
    payment_status: str
    created_at: datetime


class AddressSummary(BaseModel):
    full_name: str
    city: str
    is_default: bool = False


class CustomerDetailResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    is_active: bool
    joined_at: datetime
    order_count: int
    total_spend: float
    avg_order_value: float
    reward_points: int
    lifetime_points: int
    loyalty_tier: str
    addresses: list[AddressSummary]
    recent_orders: list[OrderSummaryItem]


class BlockCustomerResponse(BaseModel):
    id: str
    is_active: bool
    message: str


class RewardAdjustResponse(BaseModel):
    staff_id: Optional[str] = None
    customer_id: str
    points_adjusted: int
    new_balance: int
    reason: str