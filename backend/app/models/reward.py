from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RewardTransaction(BaseModel):
    type: str                    # "earn" | "redeem" | "expire" | "adjustment"
    points: int                  # positive for earn, negative for redeem/expire
    order_id: Optional[str] = None
    description: str
    created_at: datetime


class RewardModel(BaseModel):
    user_id: str
    total_points: int = 0        # current spendable balance
    lifetime_points: int = 0     # cumulative earned, never decreases — drives tier
    transactions: list[RewardTransaction] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime