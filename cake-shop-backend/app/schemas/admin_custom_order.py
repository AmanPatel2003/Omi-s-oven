from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


VALID_TRANSITIONS = {
    "pending":    ["reviewing", "rejected"],
    "reviewing":  ["quoted", "rejected"],
    "quoted":     ["confirmed", "rejected"],   # confirmed = customer accepted the quote
    "confirmed":  ["in_progress", "cancelled"],
    "in_progress":["completed", "cancelled"],
    "completed":  [],
    "rejected":   [],
    "cancelled":  [],
}


class UpdateCustomOrderStatusRequest(BaseModel):
    status: str
    admin_note: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v not in VALID_TRANSITIONS:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(VALID_TRANSITIONS.keys())}")
        return v


class SetQuoteRequest(BaseModel):
    quoted_price: float
    admin_note: Optional[str] = None

    @field_validator("quoted_price")
    @classmethod
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Quoted price must be greater than zero")
        return v


class AdminCustomOrderListItem(BaseModel):
    id: str
    request_number: str
    customer_name: str
    contact_phone: str
    occasion: str
    needed_by: datetime
    status: str
    quoted_price: Optional[float] = None
    created_at: datetime


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class AdminCustomOrderListResponse(BaseModel):
    items: list[AdminCustomOrderListItem]
    meta: PaginationMeta


class StatusHistoryResponse(BaseModel):
    status: str
    timestamp: datetime
    note: Optional[str] = None


class AdminCustomOrderDetailResponse(BaseModel):
    id: str
    request_number: str
    user_id: str
    customer_name: str
    customer_email: str
    contact_phone: str
    occasion: str
    flavor: str
    size: str
    shape: Optional[str] = None
    message_on_cake: Optional[str] = None
    reference_images: list[str]
    description: str
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    needed_by: datetime
    delivery_address_id: Optional[str] = None
    status: str
    quoted_price: Optional[float] = None
    admin_note: Optional[str] = None
    linked_order_id: Optional[str] = None
    status_history: list[StatusHistoryResponse]
    created_at: datetime