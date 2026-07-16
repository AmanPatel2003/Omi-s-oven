from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class OrderItem(BaseModel):
    product_id: str
    variant_name: Optional[str] = None
    name: str                # snapshot — product name at time of order
    image: Optional[str] = None
    price: float              # snapshot — price at time of order, immune to later changes
    qty: int
    line_total: float


class OrderAddress(BaseModel):
    full_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    landmark: Optional[str] = None


class StatusHistoryEntry(BaseModel):
    status: str
    timestamp: datetime
    note: Optional[str] = None


class OrderModel(BaseModel):
    order_number: str          # human-facing, e.g. "ORD-20260714-0001"
    user_id: str
    items: list[OrderItem]
    address: OrderAddress

    subtotal: float
    discount: float
    tax: float
    delivery_fee: float
    total: float
    coupon_code: Optional[str] = None

    status: str = "pending"    # pending -> confirmed -> preparing -> out_for_delivery -> delivered | cancelled
    payment_method: str = "cod"
    payment_status: str = "pending"   # pending | paid | failed | refunded

    status_history: list[StatusHistoryEntry] = Field(default_factory=list)
    estimated_delivery: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime