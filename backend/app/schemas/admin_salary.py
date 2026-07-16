from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
import re


def _validate_month(v: str) -> str:
    if not re.match(r"^\d{4}-\d{2}$", v):
        raise ValueError("month must be in YYYY-MM format")
    return v


class ProcessSalaryRequest(BaseModel):
    force: bool = False    # allow reprocessing an already-finalized month


class GenerateSlipRequest(BaseModel):
    email_to_staff: bool = False   # if True, attempts email dispatch (see stub note)


class AttendanceBreakdown(BaseModel):
    present_days: int
    half_days: int
    leave_days: int
    absent_days: int
    total_working_days: int


class SalaryCalculation(BaseModel):
    staff_id: str
    staff_name: str
    role: str
    month: str
    base_salary: float
    attendance: AttendanceBreakdown
    payable_days: float          # present + 0.5*half_day + leave (paid)
    prorated_salary: float
    bonus: float
    deductions: float
    net_payable: float
    already_processed: bool


class MonthSalaryPreviewResponse(BaseModel):
    month: str
    total_staff: int
    total_payable: float
    items: list[SalaryCalculation]


class ProcessSalaryResponse(BaseModel):
    month: str
    processed_count: int
    skipped_count: int
    total_paid: float
    items: list[SalaryCalculation]


class SalarySlipResponse(BaseModel):
    staff_id: str
    month: str
    pdf_generated: bool
    email_sent: bool
    email_status_note: Optional[str] = None