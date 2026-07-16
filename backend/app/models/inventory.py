from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class IngredientModel(BaseModel):
    name: str
    unit: str                          # "kg" | "g" | "l" | "ml" | "pcs"
    current_stock: float = 0
    low_stock_threshold: float = 5
    cost_per_unit: Optional[float] = None
    supplier: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class StockMovementModel(BaseModel):
    ingredient_id: str
    type: str                          # "restock" | "adjustment"
    quantity: float                     # positive = added, negative = removed
    balance_after: float
    reason: str
    reference: Optional[str] = None     # e.g. purchase invoice number
    performed_by: str                   # admin user_id
    created_at: datetime