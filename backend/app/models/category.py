from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CategoryModel(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    image: Optional[dict] = None
    parent_id: Optional[str] = None    # ← NEW: None = main category, else _id of the parent category
    sort_order: int = 0
    is_available: bool = True
    created_at: datetime
    updated_at: datetime