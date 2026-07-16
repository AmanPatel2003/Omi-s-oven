from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CategoryModel(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    image: Optional[dict] = None
    sort_order: int = 0
    is_available: bool = True
    created_at: datetime
    updated_at: datetime