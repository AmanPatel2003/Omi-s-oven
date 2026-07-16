from datetime import datetime, timedelta
from collections import defaultdict


def _default_range():
    now = datetime.utcnow()
    start = now - timedelta(days=30)
    return start, now


# ── REVENUE BREAKDOWN ────────────────────────────────────────────────
async def get_revenue_breakdown(db, date_from: datetime | None, date_to: datetime | None) -> dict:
    if not date_from or not date_to:
        date_from, date_to = _default_range()

    match_stage = {"created_at": {"$gte": date_from, "$lte": date_to}, "status": {"$ne": "cancelled"}}

    total_pipeline = [{"$match": match_stage}, {"$group": {"_id": None, "total": {"$sum": "$total"}}}]
    total_result = await db.orders.aggregate(total_pipeline).to_list(length=1)
    total_revenue = total_result[0]["total"] if total_result else 0.0

    # unwind order items to get real per-line revenue, joined against product category
    category_pipeline = [
        {"$match": match_stage},
        {"$unwind": "$items"},
        {"$lookup": {
            "from": "products",
            "let": {"pid": {"$toObjectId": "$items.product_id"}},
            "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", "$$pid"]}}}, {"$project": {"category": 1}}],
            "as": "product",
        }},
        {"$unwind": {"path": "$product", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": {"$ifNull": ["$product.category", "unknown"]},
            "revenue": {"$sum": "$items.line_total"},
            "order_count": {"$addToSet": "$_id"},
        }},
    ]
    category_results = await db.orders.aggregate(category_pipeline).to_list(length=None)

    by_category = []
    for r in category_results:
        revenue = round(r["revenue"], 2)
        by_category.append({
            "category": r["_id"],
            "revenue": revenue,
            "order_count": len(r["order_count"]),
            "percentage_of_total": round((revenue / total_revenue * 100), 1) if total_revenue else 0.0,
        })
    by_category.sort(key=lambda x: x["revenue"], reverse=True)

    # top products by actual line-item revenue (not the price*total_sold approximation from dashboard)
    product_pipeline = [
        {"$match": match_stage},
        {"$unwind": "$items"},
        {"$group": {
            "_id": "$items.product_id",
            "name": {"$first": "$items.name"},
            "revenue": {"$sum": "$items.line_total"},
            "units_sold": {"$sum": "$items.qty"},
        }},
        {"$sort": {"revenue": -1}},
        {"$limit": 10},
    ]
    product_results = await db.orders.aggregate(product_pipeline).to_list(length=10)
    top_products = [
        {
            "product_id": r["_id"],
            "name": r["name"],
            "revenue": round(r["revenue"], 2),
            "units_sold": r["units_sold"],
        }
        for r in product_results
    ]

    return {
        "period_start": date_from,
        "period_end": date_to,
        "total_revenue": round(total_revenue, 2),
        "by_category": by_category,
        "top_products_by_revenue": top_products,
    }


# ── CUSTOMER TRENDS (new vs returning) ─────────────────────────────────
async def get_customer_analytics(db, date_from: datetime | None, date_to: datetime | None) -> dict:
    if not date_from or not date_to:
        date_from, date_to = _default_range()

    # "returning" = placed an order in this window but their account was created before the window
    pipeline = [
        {"$match": {"created_at": {"$gte": date_from, "$lte": date_to}, "status": {"$ne": "cancelled"}}},
        {"$group": {
            "_id": {"day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}}, "user_id": "$user_id"},
        }},
        {"$group": {"_id": "$_id.day", "user_ids": {"$addToSet": "$_id.user_id"}}},
        {"$sort": {"_id": 1}},
    ]
    daily_orderers = await db.orders.aggregate(pipeline).to_list(length=None)

    trend = []
    total_new, total_returning = 0, 0
    for day in daily_orderers:
        new_count, returning_count = 0, 0
        for uid in day["user_ids"]:
            try:
                from bson import ObjectId
                user = await db.users.find_one({"_id": ObjectId(uid)})
            except Exception:
                user = None
            if user and user["created_at"] >= date_from:
                new_count += 1
            else:
                returning_count += 1
        trend.append({"date": day["_id"], "new_customers": new_count, "returning_customers": returning_count})
        total_new += new_count
        total_returning += returning_count

    return {
        "period_start": date_from,
        "period_end": date_to,
        "total_new": total_new,
        "total_returning": total_returning,
        "trend": trend,
    }


# ── PRODUCT SALES OVER TIME ───────────────────────────────────────────
async def get_product_sales(db, product_id: str, date_from: datetime | None, date_to: datetime | None) -> dict:
    from bson import ObjectId
    from app.core.exceptions import NotFoundException

    if not date_from or not date_to:
        date_from, date_to = _default_range()

    product = await db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise NotFoundException("Product not found")

    pipeline = [
        {"$match": {
            "created_at": {"$gte": date_from, "$lte": date_to},
            "status": {"$ne": "cancelled"},
            "items.product_id": product_id,
        }},
        {"$unwind": "$items"},
        {"$match": {"items.product_id": product_id}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "units_sold": {"$sum": "$items.qty"},
            "revenue": {"$sum": "$items.line_total"},
        }},
        {"$sort": {"_id": 1}},
    ]
    results = await db.orders.aggregate(pipeline).to_list(length=None)

    data = [
        {"date": r["_id"], "units_sold": r["units_sold"], "revenue": round(r["revenue"], 2)}
        for r in results
    ]

    return {
        "product_id": product_id,
        "product_name": product["name"],
        "period_start": date_from,
        "period_end": date_to,
        "data": data,
    }


# ── DELIVERY ANALYTICS ──────────────────────────────────────────────────
async def get_delivery_analytics(db, date_from: datetime | None, date_to: datetime | None) -> dict:
    if not date_from or not date_to:
        date_from, date_to = _default_range()

    cursor = db.deliveries.find({
        "delivered_at": {"$gte": date_from, "$lte": date_to, "$ne": None},
        "dispatched_at": {"$ne": None},
    })

    total = 0
    total_minutes = 0.0
    on_time = 0
    late = 0

    async for d in cursor:
        total += 1
        delta_minutes = (d["delivered_at"] - d["dispatched_at"]).total_seconds() / 60
        total_minutes += delta_minutes

        order = await db.orders.find_one({"_id": ObjectId(d["order_id"])})
        if order and order.get("estimated_delivery"):
            if d["delivered_at"] <= order["estimated_delivery"]:
                on_time += 1
            else:
                late += 1

    avg_minutes = round(total_minutes / total, 1) if total else None
    on_time_rate = round((on_time / (on_time + late) * 100), 1) if (on_time + late) else None

    return {
        "period_start": date_from,
        "period_end": date_to,
        "total_deliveries": total,
        "avg_delivery_time_minutes": avg_minutes,
        "on_time_rate_percent": on_time_rate,
        "late_deliveries": late,
        "note": None,
    }

# ── REWARDS ANALYTICS ─────────────────────────────────────────────────
async def get_rewards_analytics(db, date_from: datetime | None, date_to: datetime | None) -> dict:
    if not date_from or not date_to:
        date_from, date_to = _default_range()

    pipeline = [
        {"$unwind": "$transactions"},
        {"$match": {"transactions.created_at": {"$gte": date_from, "$lte": date_to}}},
        {"$group": {
            "_id": "$transactions.type",
            "total_points": {"$sum": "$transactions.points"},
        }},
    ]
    results = await db.rewards.aggregate(pipeline).to_list(length=None)
    by_type = {r["_id"]: r["total_points"] for r in results}

    points_issued = by_type.get("earn", 0)
    points_redeemed = abs(by_type.get("redeem", 0))
    points_expired = abs(by_type.get("expire", 0))

    redemption_rate = round((points_redeemed / points_issued * 100), 1) if points_issued else 0.0

    total_pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total_points"}}}]
    total_result = await db.rewards.aggregate(total_pipeline).to_list(length=1)
    net_liability = total_result[0]["total"] if total_result else 0

    return {
        "period_start": date_from,
        "period_end": date_to,
        "points_issued": points_issued,
        "points_redeemed": points_redeemed,
        "points_expired": points_expired,
        "net_liability": net_liability,
        "redemption_rate_percent": redemption_rate,
    }


# ── DEMAND FORECAST (heuristic — NOT ML, clearly labeled) ─────────────
async def get_demand_forecast(db, limit: int = 20) -> dict:
    """
    Simple weighted moving average with day-of-week seasonality.
    This is a statistical heuristic, not a trained ML model — accuracy
    depends entirely on having consistent historical sales data.
    Do not present this to stakeholders as a guaranteed prediction.
    """
    now = datetime.utcnow()
    window_start = now - timedelta(days=30)

    pipeline = [
        {"$match": {"created_at": {"$gte": window_start, "$lte": now}, "status": {"$ne": "cancelled"}}},
        {"$unwind": "$items"},
        {"$group": {
            "_id": {
                "product_id": "$items.product_id",
                "day_of_week": {"$dayOfWeek": "$created_at"},
            },
            "avg_qty": {"$avg": "$items.qty"},
            "name": {"$first": "$items.name"},
        }},
    ]
    results = await db.orders.aggregate(pipeline).to_list(length=None)

    by_product = defaultdict(lambda: {"name": "", "by_dow": {}})
    for r in results:
        pid = r["_id"]["product_id"]
        dow = r["_id"]["day_of_week"]
        by_product[pid]["name"] = r["name"]
        by_product[pid]["by_dow"][dow] = r["avg_qty"]

    # overall 30-day average as fallback for days-of-week with no data
    overall_pipeline = [
        {"$match": {"created_at": {"$gte": window_start, "$lte": now}, "status": {"$ne": "cancelled"}}},
        {"$unwind": "$items"},
        {"$group": {"_id": "$items.product_id", "total_qty": {"$sum": "$items.qty"}}},
    ]
    overall_results = await db.orders.aggregate(overall_pipeline).to_list(length=None)
    overall_avg = {r["_id"]: round(r["total_qty"] / 30, 2) for r in overall_results}

    items = []
    for pid, info in list(by_product.items())[:limit]:
        forecast_dates = []
        forecasted = []
        for i in range(1, 8):
            future_date = now + timedelta(days=i)
            dow = future_date.isoweekday() % 7 + 1   # align with Mongo's $dayOfWeek (1=Sunday)
            predicted = info["by_dow"].get(dow, overall_avg.get(pid, 0))
            forecast_dates.append(future_date.strftime("%Y-%m-%d"))
            forecasted.append(round(predicted))

        items.append({
            "product_id": pid,
            "product_name": info["name"],
            "avg_daily_sales_last_30d": overall_avg.get(pid, 0),
            "forecasted_units": forecasted,
            "forecast_dates": forecast_dates,
            "method": "day-of-week weighted average",
            "confidence_note": (
                "Heuristic estimate based on the last 30 days of sales. Not a trained "
                "forecasting model — treat as a rough planning signal, not a guarantee."
            ),
        })

    items.sort(key=lambda x: sum(x["forecasted_units"]), reverse=True)

    return {
        "generated_at": now,
        "method": "day-of-week weighted average over trailing 30 days",
        "items": items,
    }