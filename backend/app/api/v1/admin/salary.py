# GET    /admin/salary/calculate/:month   Preview salary for all staff for a month
# POST   /admin/salary/process/:month     Finalize and save salary for the month
# GET    /admin/salary/:staff_id/:month   Single staff salary breakdown
# POST   /admin/salary/:staff_id/slip     Generate and email PDF salary slip
# GET    /admin/salary/export/:month      Export all salaries as Excel sheet

import re
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.database import get_db
from app.core.dependencies import get_current_admin, get_current_super_admin
from app.core.exceptions import BadRequestException
from app.schemas.common import SuccessResponse
from app.schemas.admin_salary import (
    ProcessSalaryRequest, GenerateSlipRequest,
    MonthSalaryPreviewResponse, ProcessSalaryResponse, SalaryCalculation, SalarySlipResponse,
)
from app.services import admin_salary_service
from app.utils.helpers import success_response

router = APIRouter(dependencies=[Depends(get_current_admin)])


def _validate_month(month: str):
    if not re.match(r"^\d{4}-\d{2}$", month):
        raise BadRequestException("month must be in YYYY-MM format")


@router.get("/calculate/{month}", response_model=SuccessResponse[MonthSalaryPreviewResponse])
async def calculate_month(month: str, db=Depends(get_db)):
    _validate_month(month)
    result = await admin_salary_service.calculate_month(db=db, month=month)
    return success_response(data=result)


@router.post("/process/{month}", response_model=SuccessResponse[ProcessSalaryResponse])
async def process_month(
    month: str,
    body: ProcessSalaryRequest,
    current_admin=Depends(get_current_super_admin),   # payroll finalization — elevated
    db=Depends(get_db),
):
    _validate_month(month)
    result = await admin_salary_service.process_month(
        db=db, month=month, admin_id=current_admin["_id"], force=body.force
    )
    return success_response(data=result, message=f"Salary processed for {result['processed_count']} staff")


@router.get("/export/{month}")
async def export_salaries(month: str, db=Depends(get_db)):
    _validate_month(month)
    buffer = await admin_salary_service.export_excel(db=db, month=month)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="salary_{month}.xlsx"'},
    )


@router.get("/{staff_id}/{month}", response_model=SuccessResponse[SalaryCalculation])
async def get_staff_salary(staff_id: str, month: str, db=Depends(get_db)):
    _validate_month(month)
    result = await admin_salary_service.get_staff_salary(db=db, staff_id=staff_id, month=month)
    return success_response(data=result)


@router.post("/{staff_id}/slip", response_model=SuccessResponse[SalarySlipResponse])
async def generate_slip(
    staff_id: str,
    body: GenerateSlipRequest,
    db=Depends(get_db),
):
    # month isn't in the path per your spec — infer current month unless you want it as a query param
    from datetime import datetime
    month = datetime.utcnow().strftime("%Y-%m")

    pdf_buffer = await admin_salary_service.generate_slip_pdf(db=db, staff_id=staff_id, month=month)

    email_result = {"email_sent": False, "email_status_note": None}
    if body.email_to_staff:
        email_result = await admin_salary_service.email_slip(db=db, staff_id=staff_id, month=month, pdf_buffer=pdf_buffer)

    return success_response(data={
        "staff_id": staff_id,
        "month": month,
        "pdf_generated": True,
        **email_result,
    }, message="Salary slip generated")