from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TodayStatsResponse(BaseModel):
    revenue_today: float
    orders_today: int
    new_customers_today: int
    avg_order_value_today: float


class DailySalesPoint(BaseModel):
    day: int              # 1-31
    date: str              # "2026-07-01"
    revenue: float
    order_count: int


class DailySalesResponse(BaseModel):
    month: str             # "2026-07"
    data: list[DailySalesPoint]


class MonthlySalesPoint(BaseModel):
    month: int             # 1-12
    month_name: str
    revenue: float
    order_count: int


class MonthlySalesResponse(BaseModel):
    year: int
    data: list[MonthlySalesPoint]


class HourlyHeatmapPoint(BaseModel):
    day_of_week: int       # 1=Sunday ... 7=Saturday (Mongo $dayOfWeek convention)
    hour: int               # 0-23
    order_count: int


class HourlySalesResponse(BaseModel):
    period: str             # e.g. "last_30_days"
    data: list[HourlyHeatmapPoint]


class TopProductItem(BaseModel):
    id: str
    name: str
    slug: str
    image: Optional[str] = None
    total_sold: int
    revenue: float


class LowStockItem(BaseModel):
    id: str
    name: str
    slug: str
    stock: int
    low_stock_threshold: int
    variant_name: Optional[str] = None   # set if the low-stock hit is on a specific variant


class PendingOrderItem(BaseModel):
    id: str
    order_number: str
    customer_name: str
    total: float
    status: str
    payment_status: str
    created_at: datetime


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class PendingOrdersResponse(BaseModel):
    items: list[PendingOrderItem]
    meta: PaginationMeta
    
    
class HeatmapCell(BaseModel):
    day: int
    hour: int
    orders: int    