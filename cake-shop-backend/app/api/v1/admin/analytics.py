# GET    /admin/analytics/revenue          Revenue breakdown by category/product
# GET    /admin/analytics/customers        New vs returning customers trend
# GET    /admin/analytics/products         Sales volume per product over time
# GET    /admin/analytics/delivery         Avg delivery time, on-time rate
# GET    /admin/analytics/rewards          Points issued vs redeemed report
# GET    /admin/analytics/demand-forecast  Next 7 days demand prediction
# GET    /admin/analytics/export           Full monthly report as PDF/Excel

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.database import get_db
from app.core.dependencies import get_current_admin
from app.core.exceptions import BadRequestException
from app.schemas.common import SuccessResponse
from app.schemas.admin_analytics import (
    RevenueBreakdownResponse,
    CustomerAnalyticsResponse,
    ProductSalesResponse,
    DeliveryAnalyticsResponse,
    RewardsAnalyticsResponse,
    DemandForecastResponse,
)
from app.services import admin_analytics_service as analytics_service
from app.services import admin_export_service
from app.utils.helpers import success_response

router = APIRouter(dependencies=[Depends(get_current_admin)])


@router.get("/revenue", response_model=SuccessResponse[RevenueBreakdownResponse])
async def revenue_breakdown(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db=Depends(get_db),
):
    result = await analytics_service.get_revenue_breakdown(db=db, date_from=date_from, date_to=date_to)
    return success_response(data=result)


@router.get("/customers", response_model=SuccessResponse[CustomerAnalyticsResponse])
async def customer_analytics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db=Depends(get_db),
):
    result = await analytics_service.get_customer_analytics(db=db, date_from=date_from, date_to=date_to)
    return success_response(data=result)


@router.get("/products", response_model=SuccessResponse[ProductSalesResponse])
async def product_sales(
    product_id: str = Query(...),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db=Depends(get_db),
):
    result = await analytics_service.get_product_sales(db=db, product_id=product_id, date_from=date_from, date_to=date_to)
    return success_response(data=result)


@router.get("/delivery", response_model=SuccessResponse[DeliveryAnalyticsResponse])
async def delivery_analytics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db=Depends(get_db),
):
    result = await analytics_service.get_delivery_analytics(db=db, date_from=date_from, date_to=date_to)
    return success_response(data=result)


@router.get("/rewards", response_model=SuccessResponse[RewardsAnalyticsResponse])
async def rewards_analytics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db=Depends(get_db),
):
    result = await analytics_service.get_rewards_analytics(db=db, date_from=date_from, date_to=date_to)
    return success_response(data=result)


@router.get("/demand-forecast", response_model=SuccessResponse[DemandForecastResponse])
async def demand_forecast(
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    result = await analytics_service.get_demand_forecast(db=db, limit=limit)
    return success_response(data=result)


@router.get("/export")
async def export_report(
    format: str = Query("excel", pattern="^(excel|pdf)$"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db=Depends(get_db),
):
    if not date_from:
        now = datetime.utcnow()
        date_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if not date_to:
        date_to = datetime.utcnow()
    if date_from > date_to:
        raise BadRequestException("date_from must be before date_to")

    if format == "excel":
        buffer = await admin_export_service.export_excel(db=db, date_from=date_from, date_to=date_to)
        filename = f"report_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        buffer = await admin_export_service.export_pdf(db=db, date_from=date_from, date_to=date_to)
        filename = f"report_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.pdf"
        media_type = "application/pdf"

    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )