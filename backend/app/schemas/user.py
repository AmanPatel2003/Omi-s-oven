from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    phone: str
    role: str
    profile_photo: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class AddressRequest(BaseModel):
    full_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    # city: str
    # state: str
    # country: str
    # postal_code: str
    landmark: Optional[str] = None
    address_type: str = "Home"


class AddressResponse(AddressRequest):
    id: str
    is_default: bool = False
    created_at: datetime
    updated_at: datetime