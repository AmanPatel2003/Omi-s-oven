# GET    /admin/staff                     All staff members
# POST   /admin/staff                     Add new staff member (super_admin only)
# GET    /admin/staff/:id                 Staff profile + summary
# PUT    /admin/staff/:id                 Update staff details
# DELETE /admin/staff/:id                 Deactivate staff account (super_admin only)
# GET    /admin/staff/:id/attendance      Attendance history
# PUT    /admin/staff/:id/attendance      Mark attendance (added — required for history to have data)
# GET    /admin/staff/:id/salary-history  Salary slip history
# POST   /admin/staff/:id/salary-history  Record a salary payment (added — same reason)

from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.database import get_db
from app.core.dependencies import get_current_admin, get_current_super_admin
from app.schemas.common import SuccessResponse
from app.schemas.admin_staff import (
    CreateStaffRequest, UpdateStaffRequest, MarkAttendanceRequest, RecordSalaryRequest,
    StaffListItem, StaffDetailResponse, CreateStaffResponse,
    AttendanceHistoryResponse, SalaryHistoryResponse,
)
from app.services import admin_staff_service
from app.utils.helpers import success_response

router = APIRouter(dependencies=[Depends(get_current_admin)])   # base: any admin can read


@router.get("", response_model=SuccessResponse[list[StaffListItem]])
async def list_staff(role: Optional[str] = None, db=Depends(get_db)):
    result = await admin_staff_service.list_staff(db=db, role=role)
    return success_response(data=result)


@router.post("", response_model=SuccessResponse[CreateStaffResponse])
async def create_staff(
    body: CreateStaffRequest,
    current_admin=Depends(get_current_super_admin),   # elevated — overrides router-level dependency
    db=Depends(get_db),
):
    result = await admin_staff_service.create_staff(db=db, data=body.model_dump())
    return success_response(data=result, message="Staff member created — share the temp password securely")


@router.get("/{staff_id}", response_model=SuccessResponse[StaffDetailResponse])
async def get_staff(staff_id: str, db=Depends(get_db)):
    result = await admin_staff_service.get_staff(db=db, staff_id=staff_id)
    return success_response(data=result)


@router.put("/{staff_id}", response_model=SuccessResponse[StaffListItem])
async def update_staff(staff_id: str, body: UpdateStaffRequest, db=Depends(get_db)):
    result = await admin_staff_service.update_staff(db=db, staff_id=staff_id, data=body.model_dump(exclude_unset=True))
    return success_response(data=result, message="Staff details updated")


@router.delete("/{staff_id}", response_model=SuccessResponse[StaffListItem])
async def deactivate_staff(
    staff_id: str,
    current_admin=Depends(get_current_super_admin),
    db=Depends(get_db),
):
    result = await admin_staff_service.deactivate_staff(db=db, staff_id=staff_id)
    return success_response(data=result, message="Staff account deactivated")


@router.get("/{staff_id}/attendance", response_model=SuccessResponse[AttendanceHistoryResponse])
async def get_attendance(
    staff_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(30, ge=1, le=100),
    db=Depends(get_db),
):
    result = await admin_staff_service.get_attendance_history(db=db, staff_id=staff_id, page=page, limit=limit)
    return success_response(data=result)




@router.get("/{staff_id}/salary-history", response_model=SuccessResponse[SalaryHistoryResponse])
async def get_salary_history(
    staff_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
    db=Depends(get_db),
):
    result = await admin_staff_service.get_salary_history(db=db, staff_id=staff_id, page=page, limit=limit)
    return success_response(data=result)

