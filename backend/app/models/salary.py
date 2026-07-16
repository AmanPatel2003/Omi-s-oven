from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SalaryRecordModel(BaseModel):
    staff_id: str
    month: str                     # "2026-07"
    base_salary: float
    bonus: float = 0
    deductions: float = 0
    net_paid: float
    payment_date: datetime
    payment_method: str = "bank_transfer"
    note: Optional[str] = None
    recorded_by: str               # admin user_id
    created_at: datetime