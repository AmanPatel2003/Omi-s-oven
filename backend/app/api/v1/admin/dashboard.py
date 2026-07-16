# GET    /admin/dashboard/stats           Today's revenue, orders, new customers
# GET    /admin/dashboard/sales/daily     Revenue by day for current month
# GET    /admin/dashboard/sales/monthly   Revenue by month for current year
# GET    /admin/dashboard/sales/hourly    Orders by hour (heatmap data)
# GET    /admin/dashboard/top-products    Top 10 best-selling products
# GET    /admin/dashboard/low-stock       Products/variants below threshold
# GET    /admin/dashboard/pending-orders  All unconfirmed orders needing action

from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.common import SuccessResponse
from app.schemas.admin_dashboard import (
    TodayStatsResponse,
    DailySalesResponse,
    MonthlySalesResponse,
    HourlySalesResponse,
    TopProductItem,
    LowStockItem,
    PendingOrdersResponse,
)
from app.services import admin_dashboard_service as dashboard_service
from app.utils.helpers import success_response

# entire router gated behind admin auth — no route needs to repeat the dependency
router = APIRouter(dependencies=[Depends(get_current_admin)])


@router.get("/stats", response_model=SuccessResponse[TodayStatsResponse])
async def today_stats(db=Depends(get_db)):
    result = await dashboard_service.get_today_stats(db=db)
    return success_response(data=result)


@router.get("/sales/daily", response_model=SuccessResponse[DailySalesResponse])
async def sales_daily(db=Depends(get_db)):
    result = await dashboard_service.get_daily_sales(db=db)
    return success_response(data=result)


@router.get("/sales/monthly", response_model=SuccessResponse[MonthlySalesResponse])
async def sales_monthly(db=Depends(get_db)):
    result = await dashboard_service.get_monthly_sales(db=db)
    return success_response(data=result)


@router.get("/sales/hourly", response_model=SuccessResponse[HourlySalesResponse])
async def sales_hourly(db=Depends(get_db)):
    result = await dashboard_service.get_hourly_heatmap(db=db)
    return success_response(data=result)


@router.get("/top-products", response_model=SuccessResponse[list[TopProductItem]])
async def top_products(
    limit: int = Query(10, ge=1, le=50),
    db=Depends(get_db),
):
    result = await dashboard_service.get_top_products(db=db, limit=limit)
    return success_response(data=result)


@router.get("/low-stock", response_model=SuccessResponse[list[LowStockItem]])
async def low_stock(db=Depends(get_db)):
    result = await dashboard_service.get_low_stock(db=db)
    return success_response(data=result)


@router.get("/pending-orders", response_model=SuccessResponse[PendingOrdersResponse])
async def pending_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    result = await dashboard_service.get_pending_orders(db=db, page=page, limit=limit)
    return success_response(data=result)