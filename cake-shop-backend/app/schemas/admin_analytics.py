from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DateRangeQuery(BaseModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class CategoryRevenue(BaseModel):
    category: str
    revenue: float
    order_count: int
    percentage_of_total: float


class ProductRevenue(BaseModel):
    product_id: str
    name: str
    revenue: float
    units_sold: int


class RevenueBreakdownResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    total_revenue: float
    by_category: list[CategoryRevenue]
    top_products_by_revenue: list[ProductRevenue]


class CustomerTrendPoint(BaseModel):
    date: str
    new_customers: int
    returning_customers: int


class CustomerAnalyticsResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    total_new: int
    total_returning: int
    trend: list[CustomerTrendPoint]


class ProductSalesPoint(BaseModel):
    date: str
    units_sold: int
    revenue: float


class ProductSalesResponse(BaseModel):
    product_id: str
    product_name: str
    period_start: datetime
    period_end: datetime
    data: list[ProductSalesPoint]


class DeliveryAnalyticsResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    total_deliveries: int
    avg_delivery_time_minutes: Optional[float] = None
    on_time_rate_percent: Optional[float] = None
    late_deliveries: int
    note: Optional[str] = None


class RewardsAnalyticsResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    points_issued: int
    points_redeemed: int
    points_expired: int
    net_liability: int          # outstanding points owed to customers
    redemption_rate_percent: float


class DemandForecastItem(BaseModel):
    product_id: str
    product_name: str
    avg_daily_sales_last_30d: float
    forecasted_units: list[int]     # next 7 days
    forecast_dates: list[str]
    method: str
    confidence_note: str


class DemandForecastResponse(BaseModel):
    generated_at: datetime
    method: str
    items: list[DemandForecastItem]