from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class ClockInRequest(BaseModel):
    note: Optional[str] = None


class ClockOutRequest(BaseModel):
    note: Optional[str] = None


class PushLocationRequest(BaseModel):
    order_id: str
    lat: float
    lng: float

    @field_validator("lat")
    @classmethod
    def validate_lat(cls, v):
        if not (-90 <= v <= 90):
            raise ValueError("Invalid latitude")
        return v

    @field_validator("lng")
    @classmethod
    def validate_lng(cls, v):
        if not (-180 <= v <= 180):
            raise ValueError("Invalid longitude")
        return v


class ConfirmDeliveryRequest(BaseModel):
    otp: str

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v):
        if not v.strip().isdigit() or len(v.strip()) != 4:
            raise ValueError("OTP must be a 4-digit code")
        return v.strip()


class AttendanceRecordItem(BaseModel):
    date: str
    status: str
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    hours_worked: Optional[float] = None


class MyAttendanceResponse(BaseModel):
    month: str
    present_days: int
    half_days: int
    leave_days: int
    absent_days: int
    records: list[AttendanceRecordItem]


class SalarySlipItem(BaseModel):
    month: str
    net_paid: float
    payment_date: datetime
    payment_method: str


class MySalaryResponse(BaseModel):
    items: list[SalarySlipItem]


class AssignedOrderItem(BaseModel):
    id: str
    order_number: str
    status: str
    customer_name: str
    customer_phone: str
    address_line1: str
    city: str
    landmark: Optional[str] = None
    total: float
    item_count: int
    estimated_delivery: Optional[datetime] = None