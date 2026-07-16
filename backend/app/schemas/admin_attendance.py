from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
import re


def _validate_date_str(v: str) -> str:
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
        raise ValueError("date must be in YYYY-MM-DD format")
    try:
        datetime.strptime(v, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid date")
    return v


class ClockInRequest(BaseModel):
    staff_id: str
    date: Optional[str] = None        # defaults to today if omitted
    check_in: Optional[datetime] = None   # defaults to now if omitted
    note: Optional[str] = None

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        return _validate_date_str(v) if v else v


class ClockOutRequest(BaseModel):
    staff_id: str
    date: Optional[str] = None
    check_out: Optional[datetime] = None
    note: Optional[str] = None

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        return _validate_date_str(v) if v else v


class EditAttendanceRequest(BaseModel):
    status: Optional[str] = None
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    note: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in ("present", "absent", "half_day", "leave", "not_marked"):
            raise ValueError("Invalid status")
        return v


class MarkLeaveRequest(BaseModel):
    staff_id: str
    date_from: str
    date_to: str
    note: Optional[str] = None

    @field_validator("date_from", "date_to")
    @classmethod
    def validate_dates(cls, v):
        return _validate_date_str(v)


class AttendanceRecordResponse(BaseModel):
    id: str
    staff_id: str
    staff_name: str
    date: str
    status: str
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    hours_worked: Optional[float] = None
    note: Optional[str] = None
    is_corrected: bool


class TodayStatusItem(BaseModel):
    staff_id: str
    staff_name: str
    role: str
    status: str                       # present | absent | half_day | leave | not_marked
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None


class TodayAttendanceResponse(BaseModel):
    date: str
    total_staff: int
    present_count: int
    absent_count: int
    not_marked_count: int
    staff: list[TodayStatusItem]


class MonthlyGridDay(BaseModel):
    date: str
    status: str


class MonthlyGridRow(BaseModel):
    staff_id: str
    staff_name: str
    role: str
    days: list[MonthlyGridDay]
    present_count: int
    absent_count: int
    leave_count: int
    half_day_count: int


class MonthlyReportResponse(BaseModel):
    month: str
    rows: list[MonthlyGridRow]