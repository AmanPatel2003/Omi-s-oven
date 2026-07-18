from pydantic import BaseModel
from typing import Optional

from app.schemas.product import ProductListResponse


class CategoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    image: Optional[str] = None
    parent_id: Optional[str] = None                       # ← NEW
    subcategories: list["CategoryResponse"] = [] 


class CategoryDetailResponse(BaseModel):
    category: CategoryResponse
    products: ProductListResponse