from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime, timedelta


MIN_LEAD_TIME_HOURS = 48   # bakery needs at least 2 days' notice — adjust to your real SLA


class SubmitCustomOrderRequest(BaseModel):
    occasion: str
    flavor: str
    size: str
    shape: Optional[str] = None
    message_on_cake: Optional[str] = None
    reference_images: list[str] = []      # URLs, uploaded separately via a file-upload endpoint
    description: str
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    needed_by: datetime
    contact_phone: str
    delivery_address_id: Optional[str] = None

    @field_validator("needed_by")
    @classmethod
    def validate_lead_time(cls, v):
        if v < datetime.utcnow() + timedelta(hours=MIN_LEAD_TIME_HOURS):
            raise ValueError(f"We need at least {MIN_LEAD_TIME_HOURS} hours' notice for custom orders")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v):
        if len(v.strip()) < 10:
            raise ValueError("Please describe your requirements in a bit more detail")
        return v.strip()

    @field_validator("budget_max")
    @classmethod
    def validate_budget_range(cls, v, info):
        budget_min = info.data.get("budget_min")
        if v is not None and budget_min is not None and v < budget_min:
            raise ValueError("budget_max cannot be less than budget_min")
        return v

    @field_validator("reference_images")
    @classmethod
    def validate_image_count(cls, v):
        if len(v) > 5:
            raise ValueError("Maximum 5 reference images allowed")
        return v


class StatusHistoryResponse(BaseModel):
    status: str
    timestamp: datetime
    note: Optional[str] = None


class CustomOrderResponse(BaseModel):
    id: str
    request_number: str
    occasion: str
    flavor: str
    size: str
    shape: Optional[str] = None
    message_on_cake: Optional[str] = None
    reference_images: list[str] = []
    description: str
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    needed_by: datetime
    status: str
    quoted_price: Optional[float] = None
    created_at: datetime


class CustomOrderDetailResponse(CustomOrderResponse):
    contact_phone: str
    delivery_address_id: Optional[str] = None
    admin_note: Optional[str] = None
    status_history: list[StatusHistoryResponse]


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class CustomOrderListResponse(BaseModel):
    items: list[CustomOrderResponse]
    meta: PaginationMeta