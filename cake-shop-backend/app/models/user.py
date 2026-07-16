from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class StaffDetails(BaseModel):
    employee_id: str
    department: Optional[str] = None       # "kitchen", "delivery", "management", etc.
    designation: Optional[str] = None       # "Head Baker", "Delivery Rider", etc.
    monthly_salary: Optional[float] = None
    joining_date: datetime
    must_change_password: bool = True       # forces reset on first login

class new_user(BaseModel):
    email: str
    name: str
    phone: str
    password_hash: str
    role: str
    staff_details: Optional[StaffDetails] = None
    is_active: bool = True
    profile_photo: Optional[str] = None
    addresses: list = Field(default_factory=list)

    created_at: datetime
    updated_at: datetime
    
