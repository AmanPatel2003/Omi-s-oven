from pydantic import BaseModel, field_validator
from typing import Optional


class AddCartItemRequest(BaseModel):
    product_id: str
    variant_name: Optional[str] = None
    qty: int = 1

    @field_validator("qty")
    @classmethod
    def validate_qty(cls, v):
        if v < 1:
            raise ValueError("Quantity must be at least 1")
        if v > 50:
            raise ValueError("Quantity cannot exceed 50")
        return v


class UpdateCartItemRequest(BaseModel):
    product_id: str
    variant_name: Optional[str] = None
    qty: int

    @field_validator("qty")
    @classmethod
    def validate_qty(cls, v):
        if v < 0:
            raise ValueError("Quantity cannot be negative")
        if v > 50:
            raise ValueError("Quantity cannot exceed 50")
        return v


class ApplyCouponRequest(BaseModel):
    code: str

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v):
        return v.strip().upper()


class CartItemResponse(BaseModel):
    product_id: str
    variant_name: Optional[str] = None
    name: str
    image: Optional[str] = None
    price: float
    qty: int
    line_total: float
    in_stock: bool
    available_stock: int


class CartResponse(BaseModel):
    items: list[CartItemResponse]
    applied_coupon: Optional[str] = None
    item_count: int


class CartSummaryResponse(BaseModel):
    subtotal: float
    discount: float
    tax: float
    delivery_fee: float
    total: float
    applied_coupon: Optional[str] = None
    item_count: int