from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class SortOption(str, Enum):
    price_asc = "price_asc"
    price_desc = "price_desc"
    newest = "newest"
    bestselling = "bestselling"
    rating = "rating"


class ProductImageResponse(BaseModel):
    url: str
    public_id: str

class ProductResponse(BaseModel):
    id: str
    name: str
    slug: str
    category: str
    price: float
    discount_price: Optional[float] = None
    images: list[ProductImageResponse]= []
    tags: list[str] = []
    is_eggless: bool
    stock: int
    avg_rating: float
    review_count: int
    total_sold: int


class ProductDetailResponse(ProductResponse):
    description: str
    is_featured: bool
    created_at: datetime


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    meta: PaginationMeta


class ReviewRequest(BaseModel):
    rating: int
    comment: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v):
        if not (1 <= v <= 5):
            raise ValueError("Rating must be between 1 and 5")
        return v

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, v):
        if v is not None and len(v.strip()) > 1000:
            raise ValueError("Comment must be under 1000 characters")
        return v.strip() if v else v


class ReviewResponse(BaseModel):
    id: str
    product_id: str
    user_id: str
    user_name: str
    rating: int
    comment: Optional[str] = None
    created_at: datetime


class ReviewListResponse(BaseModel):
    items: list[ReviewResponse]
    meta: PaginationMeta