from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
import re
import secrets
import string


class CreateStaffRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    role: str                       # "admin" | "delivery_staff"
    department: Optional[str] = None
    designation: Optional[str] = None
    monthly_salary: Optional[float] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in ("admin", "delivery_staff"):
            raise ValueError("role must be 'admin' or 'delivery_staff'")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if not re.match(r"^[6-9]\d{9}$", v.strip()):
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return v.strip()


class UpdateStaffRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    monthly_salary: Optional[float] = None


class MarkAttendanceRequest(BaseModel):
    date: str                       # "2026-07-16"
    status: str
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    note: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v not in ("present", "absent", "half_day", "leave"):
            raise ValueError("status must be present, absent, half_day, or leave")
        return v

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("date must be in YYYY-MM-DD format")
        return v


class RecordSalaryRequest(BaseModel):
    month: str                      # "2026-07"
    base_salary: float
    bonus: float = 0
    deductions: float = 0
    payment_date: datetime
    payment_method: str = "bank_transfer"
    note: Optional[str] = None

    @field_validator("month")
    @classmethod
    def validate_month(cls, v):
        if not re.match(r"^\d{4}-\d{2}$", v):
            raise ValueError("month must be in YYYY-MM format")
        return v

    @field_validator("base_salary")
    @classmethod
    def validate_base(cls, v):
        if v < 0:
            raise ValueError("base_salary cannot be negative")
        return v


class StaffListItem(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    role: str
    department: Optional[str] = None
    designation: Optional[str] = None
    is_active: bool
    joining_date: Optional[datetime] = None


class StaffDetailResponse(StaffListItem):
    monthly_salary: Optional[float] = None
    attendance_this_month: dict          # {"present": N, "absent": N, "leave": N, "half_day": N}
    total_deliveries: Optional[int] = None    # only meaningful for delivery_staff


class CreateStaffResponse(BaseModel):
    staff: StaffListItem
    temp_password: str            # shown once — admin must relay this to the staff member securely


class AttendanceRecordResponse(BaseModel):
    date: str
    status: str
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    note: Optional[str] = None


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class AttendanceHistoryResponse(BaseModel):
    staff_id: str
    items: list[AttendanceRecordResponse]
    meta: PaginationMeta


class SalaryRecordResponse(BaseModel):
    month: str
    base_salary: float
    bonus: float
    deductions: float
    net_paid: float
    payment_date: datetime
    payment_method: str
    note: Optional[str] = None


class SalaryHistoryResponse(BaseModel):
    staff_id: str
    items: list[SalaryRecordResponse]
    meta: PaginationMeta


def generate_temp_password() -> str:
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(10))