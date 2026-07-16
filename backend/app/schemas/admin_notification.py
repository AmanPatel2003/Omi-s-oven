from pydantic import BaseModel, field_validator
from typing import Optional


VALID_CHANNELS = {"email", "sms", "whatsapp"}


class SegmentFilter(BaseModel):
    """Optional targeting filter — used by both send and broadcast."""
    loyalty_tier: Optional[str] = None                 # "Silver" | "Gold" | "Platinum"
    inactive_days: Optional[int] = None                 # hasn't ordered in N days
    min_lifetime_orders: Optional[int] = None


class SendNotificationRequest(BaseModel):
    channel: str
    customer_ids: Optional[list[str]] = None    # explicit targeting
    segment: Optional[SegmentFilter] = None       # OR filtered targeting — one of the two required
    subject: Optional[str] = None                  # required if channel == "email"
    message: str

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, v):
        if v not in VALID_CHANNELS:
            raise ValueError(f"channel must be one of: {', '.join(VALID_CHANNELS)}")
        return v

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        if len(v.strip()) < 5:
            raise ValueError("Message is too short")
        return v.strip()


class BroadcastRequest(BaseModel):
    channel: str
    subject: Optional[str] = None
    message: str
    exclude_inactive: bool = True    # skip blocked/deactivated accounts by default

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, v):
        if v not in VALID_CHANNELS:
            raise ValueError(f"channel must be one of: {', '.join(VALID_CHANNELS)}")
        return v

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        if len(v.strip()) < 5:
            raise ValueError("Message is too short")
        return v.strip()


class CampaignResponse(BaseModel):
    id: str
    type: str
    channel: str
    subject: Optional[str] = None
    message: str
    target_count: int
    sent_count: int
    failed_count: int
    skipped_count: int
    status: str
    provider_configured: bool
    warning: Optional[str] = None