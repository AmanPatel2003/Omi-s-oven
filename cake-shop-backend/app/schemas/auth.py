from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import re
# ── REQUEST SCHEMAS (defined here to keep schemas/auth.py clean) ──

class RegisterRequest(BaseModel):  
    name: str
    email: EmailStr
    phone: str
    password: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if not re.match(r"^[6-9]\d{9}$", v.strip()):
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return v.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()


class LoginRequest(BaseModel):
    identifier: str    # accepts email OR phone number
    password: str

class GoogleLoginRequest(BaseModel):
    token: str

class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError("New password must be at least 8 characters")
        return v
