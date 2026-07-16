from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LocationPing(BaseModel):
    lat: float
    lng: float
    timestamp: datetime


class DeliveryModel(BaseModel):
    order_id: str
    rider_id: Optional[str] = None          # set when admin assigns a rider
    otp: Optional[str] = None                # generated at dispatch, shown to customer via SMS
    otp_verified: bool = False

    current_location: Optional[LocationPing] = None
    location_history: list[LocationPing] = Field(default_factory=list)

    delivered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime