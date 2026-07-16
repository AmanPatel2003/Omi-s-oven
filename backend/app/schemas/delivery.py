from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class UpdateLocationRequest(BaseModel):
    order_id: str
    lat: float
    lng: float

    @field_validator("lat")
    @classmethod
    def validate_lat(cls, v):
        if not (-90 <= v <= 90):
            raise ValueError("Invalid latitude")
        return v

    @field_validator("lng")
    @classmethod
    def validate_lng(cls, v):
        if not (-180 <= v <= 180):
            raise ValueError("Invalid longitude")
        return v


class ConfirmDeliveryRequest(BaseModel):
    otp: str

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v):
        if not v.strip().isdigit() or len(v.strip()) != 4:
            raise ValueError("OTP must be a 4-digit code")
        return v.strip()


class LocationResponse(BaseModel):
    lat: float
    lng: float
    timestamp: datetime


class TrackDeliveryResponse(BaseModel):
    order_id: str
    order_status: str
    current_location: Optional[LocationResponse] = None
    estimated_delivery: Optional[datetime] = None
    delivered_at: Optional[datetime] = None