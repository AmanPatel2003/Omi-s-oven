# GET    /admin/attendance/today          All staff clock-in status for today
# GET    /admin/attendance/report         Monthly attendance grid (all staff)
# POST   /admin/attendance/clock-in       Record clock-in for a staff member
# POST   /admin/attendance/clock-out      Record clock-out + calculate hours
# PUT    /admin/attendance/:id            Edit attendance record (correction)
# POST   /admin/attendance/mark-leave     Mark leave for staff member
# GET    /admin/attendance/export         Export attendance sheet as Excel

import re
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.database import get_db
from app.core.dependencies import get_current_admin
from app.core.exceptions import BadRequestException
from app.schemas.common import SuccessResponse
from app.schemas.admin_attendance import (
    ClockInRequest, ClockOutRequest, EditAttendanceRequest, MarkLeaveRequest,
    AttendanceRecordResponse, TodayAttendanceResponse, MonthlyReportResponse,
)
from app.services import admin_attendance_service
from app.utils.helpers import success_response

router = APIRouter(dependencies=[Depends(get_current_admin)])


def _validate_month(month: str):
    if not re.match(r"^\d{4}-\d{2}$", month):
        raise BadRequestException("month must be in YYYY-MM format")


# ── STATIC ROUTES FIRST ─────────────────────────────────────────────

@router.get("/today", response_model=SuccessResponse[TodayAttendanceResponse])
async def today_status(db=Depends(get_db)):
    result = await admin_attendance_service.get_today_status(db=db)
    return success_response(data=result)


@router.get("/report", response_model=SuccessResponse[MonthlyReportResponse])
async def monthly_report(
    month: str = Query(..., description="YYYY-MM"),
    db=Depends(get_db),
):
    _validate_month(month)
    result = await admin_attendance_service.get_monthly_report(db=db, month=month)
    return success_response(data=result)


@router.get("/export")
async def export_attendance(
    month: str = Query(..., description="YYYY-MM"),
    db=Depends(get_db),
):
    _validate_month(month)
    buffer = await admin_attendance_service.export_excel(db=db, month=month)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="attendance_{month}.xlsx"'},
    )


@router.post("/clock-in", response_model=SuccessResponse[AttendanceRecordResponse])
async def clock_in(
    body: ClockInRequest,
    current_admin=Depends(get_current_admin),
    db=Depends(get_db),
):
    result = await admin_attendance_service.clock_in(
        db=db, staff_id=body.staff_id, admin_id=current_admin["_id"],
        date=body.date, check_in=body.check_in, note=body.note,
    )
    return success_response(data=result, message="Clock-in recorded")


@router.post("/clock-out", response_model=SuccessResponse[AttendanceRecordResponse])
async def clock_out(
    body: ClockOutRequest,
    current_admin=Depends(get_current_admin),
    db=Depends(get_db),
):
    result = await admin_attendance_service.clock_out(
        db=db, staff_id=body.staff_id, admin_id=current_admin["_id"],
        date=body.date, check_out=body.check_out, note=body.note,
    )
    return success_response(data=result, message="Clock-out recorded")


@router.post("/mark-leave", response_model=SuccessResponse[list[AttendanceRecordResponse]])
async def mark_leave(
    body: MarkLeaveRequest,
    current_admin=Depends(get_current_admin),
    db=Depends(get_db),
):
    result = await admin_attendance_service.mark_leave(
        db=db, staff_id=body.staff_id, admin_id=current_admin["_id"],
        date_from=body.date_from, date_to=body.date_to, note=body.note,
    )
    return success_response(data=result, message="Leave marked")


# ── DYNAMIC {id} — must be LAST ──────────────────────────────────────

@router.put("/{attendance_id}", response_model=SuccessResponse[AttendanceRecordResponse])
async def edit_attendance(
    attendance_id: str,
    body: EditAttendanceRequest,
    current_admin=Depends(get_current_admin),
    db=Depends(get_db),
):
    result = await admin_attendance_service.edit_attendance(
        db=db, attendance_id=attendance_id, admin_id=current_admin["_id"],
        data=body.model_dump(exclude_unset=True),
    )
    return success_response(data=result, message="Attendance record corrected")