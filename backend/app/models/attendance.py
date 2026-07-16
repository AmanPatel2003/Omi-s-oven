from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AttendanceModel(BaseModel):
    staff_id: str
    date: str                      # "2026-07-16" — one record per staff per day, enforced by unique index
    status: str                     # "present" | "absent" | "half_day" | "leave" | "not_marked"
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    hours_worked: Optional[float] = None
    note: Optional[str] = None
    marked_by: str                  # admin user_id who recorded/edited this
    is_corrected: bool = False       # true if this record was manually edited after creation
    created_at: datetime
    updated_at: datetime