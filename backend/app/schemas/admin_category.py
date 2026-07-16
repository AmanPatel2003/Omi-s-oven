from pydantic import BaseModel, field_validator
from typing import Optional


class CreateCategoryRequest(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    sort_order: int = 0

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v):
        v = v.strip().lower().replace(" ", "-")
        if not v:
            raise ValueError("Slug cannot be empty")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()


class UpdateCategoryRequest(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v):
        if v is not None:
            v = v.strip().lower().replace(" ", "-")
        return v


class ReorderItem(BaseModel):
    id: str
    sort_order: int


class ReorderCategoriesRequest(BaseModel):
    items: list[ReorderItem]

    @field_validator("items")
    @classmethod
    def validate_items(cls, v):
        if not v:
            raise ValueError("At least one item required")
        ids = [item.id for item in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate category ids in reorder request")
        return v


class CategoryImageResponse(BaseModel):
    url: str
    public_id: str


class AdminCategoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    image: Optional[CategoryImageResponse] = None
    sort_order: int
    is_active: bool
    product_count: int = 0