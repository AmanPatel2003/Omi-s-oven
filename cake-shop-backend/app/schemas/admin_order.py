from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


VALID_TRANSITIONS = {
    "pending":          ["confirmed", "cancelled"],
    "confirmed":        ["preparing", "cancelled"],
    "preparing":        ["out_for_delivery", "cancelled"],
    "out_for_delivery": ["delivered", "cancelled"],
    "delivered":        [],       # terminal
    "cancelled":        [],       # terminal
}


class UpdateOrderStatusRequest(BaseModel):
    status: str
    note: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v not in VALID_TRANSITIONS:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(VALID_TRANSITIONS.keys())}")
        return v


class AssignDeliveryRequest(BaseModel):
    rider_id: str


class AdminOrderListItem(BaseModel):
    id: str
    order_number: str
    customer_name: str
    customer_phone: str
    total: float
    status: str
    payment_status: str
    payment_method: str
    item_count: int
    created_at: datetime


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class AdminOrderListResponse(BaseModel):
    items: list[AdminOrderListItem]
    meta: PaginationMeta


class AdminOrderItemResponse(BaseModel):
    product_id: str
    variant_name: Optional[str] = None
    name: str
    image: Optional[str] = None
    price: float
    qty: int
    line_total: float


class AdminOrderAddressResponse(BaseModel):
    full_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    landmark: Optional[str] = None


class StatusHistoryResponse(BaseModel):
    status: str
    timestamp: datetime
    note: Optional[str] = None


class AdminOrderDetailResponse(BaseModel):
    id: str
    order_number: str
    user_id: str
    customer_email: Optional[str] = None
    items: list[AdminOrderItemResponse]
    address: AdminOrderAddressResponse
    subtotal: float
    discount: float
    tax: float
    delivery_fee: float
    total: float
    coupon_code: Optional[str] = None
    status: str
    payment_method: str
    payment_status: str
    assigned_rider_id: Optional[str] = None
    assigned_rider_name: Optional[str] = None
    status_history: list[StatusHistoryResponse]
    estimated_delivery: Optional[datetime] = None
    created_at: datetime