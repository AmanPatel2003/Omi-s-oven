from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


VALID_UNITS = {"kg", "g", "l", "ml", "pcs"}


class CreateIngredientRequest(BaseModel):
    name: str
    unit: str
    current_stock: float = 0
    low_stock_threshold: float = 5
    cost_per_unit: Optional[float] = None
    supplier: Optional[str] = None

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, v):
        if v not in VALID_UNITS:
            raise ValueError(f"Unit must be one of: {', '.join(VALID_UNITS)}")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()

    @field_validator("current_stock", "low_stock_threshold")
    @classmethod
    def validate_non_negative(cls, v):
        if v < 0:
            raise ValueError("Cannot be negative")
        return v


class UpdateIngredientRequest(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    low_stock_threshold: Optional[float] = None
    cost_per_unit: Optional[float] = None
    supplier: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, v):
        if v is not None and v not in VALID_UNITS:
            raise ValueError(f"Unit must be one of: {', '.join(VALID_UNITS)}")
        return v


class RestockRequest(BaseModel):
    quantity: float
    cost_per_unit: Optional[float] = None    # optional — update the ingredient's cost if this purchase differs
    reference: Optional[str] = None           # invoice/PO number
    reason: str = "Restock"

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError("Restock quantity must be greater than zero")
        return v


class AdjustStockRequest(BaseModel):
    quantity: float          # can be negative (wastage/spoilage/correction down) or positive (correction up)
    reason: str

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        if v == 0:
            raise ValueError("Adjustment quantity cannot be zero")
        return v

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v):
        if len(v.strip()) < 3:
            raise ValueError("Please provide a reason for this adjustment")
        return v.strip()


class IngredientResponse(BaseModel):
    id: str
    name: str
    unit: str
    current_stock: float
    low_stock_threshold: float
    cost_per_unit: Optional[float] = None
    supplier: Optional[str] = None
    is_active: bool
    is_low_stock: bool


class MovementResponse(BaseModel):
    id: str
    ingredient_id: str
    type: str
    quantity: float
    balance_after: float
    reason: str
    reference: Optional[str] = None
    performed_by_name: Optional[str] = None
    created_at: datetime


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class MovementListResponse(BaseModel):
    items: list[MovementResponse]
    meta: PaginationMeta