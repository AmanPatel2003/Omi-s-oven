from datetime import datetime, timedelta, timezone
from calendar import month_name



VALID_REVENUE_STATUSES = {"$ne": "cancelled"}   # orders counted as revenue: everything except cancelled
PENDING_ACTION_STATUSES = ["pending"]            # orders needing admin action right now


def _day_bounds_utc(dt: datetime):
    start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end


# ── TODAY'S STATS ────────────────────────────────────────────────
async def get_today_stats(db) -> dict:
    now = datetime.utcnow()
    start, end = _day_bounds_utc(now)

    order_query = {"created_at": {"$gte": start, "$lt": end}, "status": VALID_REVENUE_STATUSES}

    pipeline = [
        {"$match": order_query},
        {"$group": {
            "_id": None,
            "revenue": {"$sum": "$total"},
            "order_count": {"$sum": 1},
        }},
    ]
    result = await db.orders.aggregate(pipeline).to_list(length=1)
    revenue = result[0]["revenue"] if result else 0.0
    order_count = result[0]["order_count"] if result else 0

    new_customers_today = await db.users.count_documents({
        "created_at": {"$gte": start, "$lt": end},
        "role": "customer",
    })

    avg_order_value = round(revenue / order_count, 2) if order_count else 0.0

    return {
        "revenue_today": round(revenue, 2),
        "orders_today": order_count,
        "new_customers_today": new_customers_today,
        "avg_order_value_today": avg_order_value,
    }


# ── DAILY SALES (current month) ────────────────────────────────────
async def get_daily_sales(db) -> dict:
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # first day of next month, handles Dec -> Jan rollover
    next_month = month_start.replace(year=month_start.year + 1, month=1) if month_start.month == 12 \
        else month_start.replace(month=month_start.month + 1)

    pipeline = [
        {"$match": {
            "created_at": {"$gte": month_start, "$lt": next_month},
            "status": VALID_REVENUE_STATUSES,
        }},
        {"$group": {
            "_id": {"$dayOfMonth": "$created_at"},
            "revenue": {"$sum": "$total"},
            "order_count": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ]
    results = await db.orders.aggregate(pipeline).to_list(length=31)
    by_day = {r["_id"]: r for r in results}

    import calendar
    days_in_month = calendar.monthrange(now.year, now.month)[1]

    data = []
    for day in range(1, days_in_month + 1):
        r = by_day.get(day)
        data.append({
            "day": day,
            "date": f"{now.year}-{now.month:02d}-{day:02d}",
            "revenue": round(r["revenue"], 2) if r else 0.0,
            "order_count": r["order_count"] if r else 0,
        })

    return {"month": f"{now.year}-{now.month:02d}", "data": data}


# ── MONTHLY SALES (current year) ───────────────────────────────────
async def get_monthly_sales(db) -> dict:
    now = datetime.utcnow()
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    year_end = year_start.replace(year=year_start.year + 1)

    pipeline = [
        {"$match": {
            "created_at": {"$gte": year_start, "$lt": year_end},
            "status": VALID_REVENUE_STATUSES,
        }},
        {"$group": {
            "_id": {"$month": "$created_at"},
            "revenue": {"$sum": "$total"},
            "order_count": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ]
    results = await db.orders.aggregate(pipeline).to_list(length=12)
    by_month = {r["_id"]: r for r in results}

    data = []
    for m in range(1, 13):
        r = by_month.get(m)
        data.append({
            "month": m,
            "month_name": month_name[m],
            "revenue": round(r["revenue"], 2) if r else 0.0,
            "order_count": r["order_count"] if r else 0,
        })

    return {"year": now.year, "data": data}


# ── HOURLY HEATMAP (day-of-week x hour, trailing 30 days) ─────────
async def get_hourly_heatmap(db) -> dict:
    now = datetime.utcnow()
    window_start = now - timedelta(days=30)

    pipeline = [
        {"$match": {"created_at": {"$gte": window_start, "$lte": now}}},
        {"$group": {
            "_id": {
                "day_of_week": {"$dayOfWeek": "$created_at"},  # 1=Sunday..7=Saturday
                "hour": {"$hour": "$created_at"},
            },
            "order_count": {"$sum": 1},
        }},
    ]
    results = await db.orders.aggregate(pipeline).to_list(length=None)

    data = [
        {
            "day_of_week": r["_id"]["day_of_week"],
            "hour": r["_id"]["hour"],
            "order_count": r["order_count"],
        }
        for r in results
    ]
    return {"period": "last_30_days", "data": data}


# ── TOP PRODUCTS ────────────────────────────────────────────────────
async def get_top_products(db, limit: int = 10) -> list:
    cursor = db.products.find(
        {"is_available": True, "total_sold": {"$gt": 0}}
    ).sort([("total_sold", -1)]).limit(limit)

    items = []
    async for p in cursor:
        price = p.get("discount_price") or p["price"]
        items.append({
            "id": str(p["_id"]),
            "name": p["name"],
            "slug": p["slug"],
            "image": p["images"][0] if p.get("images") else None,
            "total_sold": p.get("total_sold", 0),
            "revenue": round(price * p.get("total_sold", 0), 2),   # approximation — see note below
        })
    return items


# ── LOW STOCK ─────────────────────────────────────────────────────
async def get_low_stock(db) -> list:
    items = []

    # base products (no variants)
    cursor = db.products.find({
        "is_available": True,
        "$expr": {"$lte": ["$stock", "$low_stock_threshold"]},
    })
    async for p in cursor:
        items.append({
            "id": str(p["_id"]),
            "name": p["name"],
            "slug": p["slug"],
            "stock": p["stock"],
            "low_stock_threshold": p.get("low_stock_threshold", 10),
            "variant_name": None,
        })

    # products with variants — check each variant individually
    cursor = db.products.find({"is_available": True, "variants": {"$exists": True, "$ne": []}})
    async for p in cursor:
        threshold = p.get("low_stock_threshold", 10)
        for v in p.get("variants", []):
            if v.get("stock", 0) <= threshold:
                items.append({
                    "id": str(p["_id"]),
                    "name": p["name"],
                    "slug": p["slug"],
                    "stock": v["stock"],
                    "low_stock_threshold": threshold,
                    "variant_name": v["name"],
                })

    return sorted(items, key=lambda x: x["stock"])   # most urgent first


# ── PENDING ORDERS ──────────────────────────────────────────────────
async def get_pending_orders(db, page: int = 1, limit: int = 20) -> dict:
    page = max(page, 1)
    limit = min(max(limit, 1), 100)
    skip = (page - 1) * limit

    query = {"status": {"$in": PENDING_ACTION_STATUSES}}
    total = await db.orders.count_documents(query)

    cursor = db.orders.find(query).sort([("created_at", 1)]).skip(skip).limit(limit)  # oldest first — FIFO action queue

    items = []
    async for o in cursor:
        items.append({
            "id": str(o["_id"]),
            "order_number": o["order_number"],
            "customer_name": o["address"]["full_name"],   # snapshot name from order, no extra user lookup needed
            "total": o["total"],
            "status": o["status"],
            "payment_status": o["payment_status"],
            "created_at": o["created_at"],
        })

    return {
        "items": items,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total else 0,
        },
    }
    
    
    


async def get_hourly_heatmap(db):
    start_date = datetime.utcnow() - timedelta(days=30)

    pipeline = [
        {
            "$match": {
                "created_at": {"$gte": start_date}
            }
        },
        {
            "$group": {
                "_id": {
                    "day": {"$dayOfWeek": "$created_at"},
                    "hour": {"$hour": "$created_at"},
                },
                "orders": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "day": {"$subtract": ["$_id.day", 1]},
                "hour": "$_id.hour",
                "orders": "$orders",
            }
        },
        {
            "$sort": {
                "day": 1,
                "hour": 1,
            }
        },
    ]

    return await db.orders.aggregate(pipeline).to_list(None)