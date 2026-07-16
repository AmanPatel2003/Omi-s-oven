from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class RedeemPointsRequest(BaseModel):
    points: int

    @field_validator("points")
    @classmethod
    def validate_points(cls, v):
        if v <= 0:
            raise ValueError("Points must be greater than zero")
        return v


class RewardBalanceResponse(BaseModel):
    total_points: int
    lifetime_points: int
    current_tier: str
    next_tier: Optional[str] = None
    points_to_next_tier: Optional[int] = None
    redeemed_points_on_cart: int = 0
    redeemed_value_on_cart: float = 0.0


class TransactionResponse(BaseModel):
    type: str
    points: int
    order_id: Optional[str] = None
    description: str
    created_at: datetime


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    meta: PaginationMeta


class TierInfo(BaseModel):
    name: str
    min_lifetime_points: int
    benefits: list[str]


class TiersResponse(BaseModel):
    tiers: list[TierInfo]
    point_value: str    # human-readable, e.g. "1 point = ₹1"


class RedeemResponse(BaseModel):
    redeemed_points: int
    discount_value: float
    remaining_balance: int