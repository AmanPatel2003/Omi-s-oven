from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class PlaceOrderRequest(BaseModel):
    address_id: str            # references a saved address in the user's profile
    payment_method: str = "cod"   # "cod" | "online" — extend once you add a payment gateway
    note: Optional[str] = None

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, v):
        if v not in ("cod", "online"):
            raise ValueError("payment_method must be 'cod' or 'online'")
        return v


class OrderItemResponse(BaseModel):
    product_id: str
    variant_name: Optional[str] = None
    name: str
    image: Optional[str] = None
    price: float
    qty: int
    line_total: float


class OrderAddressResponse(BaseModel):
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


class OrderResponse(BaseModel):
    id: str
    order_number: str
    items: list[OrderItemResponse]
    address: OrderAddressResponse
    subtotal: float
    discount: float
    tax: float
    delivery_fee: float
    total: float
    coupon_code: Optional[str] = None
    status: str
    payment_method: str
    payment_status: str
    estimated_delivery: Optional[datetime] = None
    created_at: datetime


class OrderDetailResponse(OrderResponse):
    status_history: list[StatusHistoryResponse]


class OrderTrackingResponse(BaseModel):
    order_number: str
    status: str
    status_history: list[StatusHistoryResponse]
    estimated_delivery: Optional[datetime] = None


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    meta: PaginationMeta


class ReorderResponse(BaseModel):
    added: list[str]        # product names successfully added to cart
    skipped: list[str]      # product names skipped (out of stock / removed)