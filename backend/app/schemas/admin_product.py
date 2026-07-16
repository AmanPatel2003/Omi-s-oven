from pydantic import BaseModel, field_validator
from typing import Optional


class ProductVariantInput(BaseModel):
    name: str
    price: float
    stock: int = 0


class CreateProductRequest(BaseModel):
    name: str
    slug: str
    description: str
    category: str
    price: float
    discount_price: Optional[float] = None
    tags: list[str] = []
    variants: list[ProductVariantInput] = []
    is_eggless: bool = False
    stock: int = 0
    low_stock_threshold: int = 10

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v):
        v = v.strip().lower().replace(" ", "-")
        if not v:
            raise ValueError("Slug cannot be empty")
        return v

    @field_validator("price")
    @classmethod
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Price must be greater than zero")
        return v

    @field_validator("discount_price")
    @classmethod
    def validate_discount(cls, v, info):
        price = info.data.get("price")
        if v is not None and price is not None and v >= price:
            raise ValueError("Discount price must be less than the regular price")
        return v


class UpdateProductRequest(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    discount_price: Optional[float] = None
    tags: Optional[list[str]] = None
    is_eggless: Optional[bool] = None
    low_stock_threshold: Optional[int] = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v):
        if v is not None:
            v = v.strip().lower().replace(" ", "-")
        return v


class UpdateStockRequest(BaseModel):
    variant_name: Optional[str] = None   # None = base product stock (no variants)
    stock: int

    @field_validator("stock")
    @classmethod
    def validate_stock(cls, v):
        if v < 0:
            raise ValueError("Stock cannot be negative")
        return v


class ProductImageResponse(BaseModel):
    url: str
    public_id: str


class AdminProductResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    category: str
    price: float
    discount_price: Optional[float] = None
    images: list[ProductImageResponse]
    tags: list[str]
    variants: list[ProductVariantInput]
    is_eggless: bool
    stock: int
    low_stock_threshold: int
    is_available: bool
    is_featured: bool
    total_sold: int
    avg_rating: float
    review_count: int