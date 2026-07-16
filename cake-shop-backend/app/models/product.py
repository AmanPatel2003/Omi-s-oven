from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ProductModel(BaseModel):
    name: str
    slug: str
    description: str
    category: str          # category slug e.g. "cakes"
    price: float
    discount_price: Optional[float] = None
    images: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)     # e.g. ["bestseller", "new"]
    is_eggless: bool = False
    stock: int = 0
    is_featured: bool = False
    is_available: bool = True   

    total_sold: int = 0
    avg_rating: float = 0.0
    review_count: int = 0

    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    low_stock_threshold: int = 10   # add this line — alert when stock drops below this


class ReviewModel(BaseModel):
    product_id: str
    user_id: str
    user_name: str
    rating: int          # 1-5
    comment: Optional[str] = None
    created_at: datetime
    
class ProductVariant(BaseModel):
    name: str            # e.g. "500g", "1kg"
    price: float
    stock: int


class ProductImage(BaseModel):
    url: str
    public_id: str        # needed for Cloudinary deletion — never expose deletion without this


