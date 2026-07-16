from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import connect_db, disconnect_db
from app.core.exceptions import AppException, app_exception_handler

# ── Customer routes
from app.api.v1 import (
    auth, users, products, categories,
    cart, orders, payments, delivery,
    rewards, coupons, custom_orders,
    notifications, reviews, staff_app,
)

# ── Admin routes
from app.api.v1.admin import (
    dashboard, orders as admin_orders,
    products as admin_products,
    categories as admin_categories,
    inventory, coupons as admin_coupons,
    custom_orders as admin_custom_orders,
    analytics, staff, attendance,
    salary, customers, notifications as admin_notifications,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global exception handler ──────────────────────────────────
app.add_exception_handler(AppException, app_exception_handler)

# ── Health check
@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "app": settings.APP_NAME}

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}

# ── Customer routers
PREFIX = "/api/v1"
app.include_router(auth.router,          prefix=f"{PREFIX}/auth",         tags=["Auth"])
app.include_router(users.router,         prefix=f"{PREFIX}/users",        tags=["Users"])
app.include_router(products.router,      prefix=f"{PREFIX}/products",     tags=["Products"])
app.include_router(categories.router,    prefix=f"{PREFIX}/categories",   tags=["Categories"])
app.include_router(cart.router,          prefix=f"{PREFIX}/cart",         tags=["Cart"])
app.include_router(orders.router,        prefix=f"{PREFIX}/orders",       tags=["Orders"])
app.include_router(custom_orders.router, prefix=f"{PREFIX}/custom-orders",tags=["Custom Orders"])
# app.include_router(payments.router,      prefix=f"{PREFIX}/payments",     tags=["Payments"])
app.include_router(delivery.router,      prefix=f"{PREFIX}/delivery",     tags=["Delivery"])
app.include_router(rewards.router,       prefix=f"{PREFIX}/rewards",      tags=["Rewards"])
app.include_router(coupons.router,       prefix=f"{PREFIX}/coupons",      tags=["Coupons"])
app.include_router(notifications.router, prefix=f"{PREFIX}/notifications", tags=["Notifications"])
# app.include_router(reviews.router,       prefix=f"{PREFIX}/reviews",      tags=["Reviews"])
app.include_router(staff_app.router,     prefix=f"{PREFIX}/staff",        tags=["Staff App"])

# ── Admin routers
ADMIN = f"{PREFIX}/admin"
app.include_router(dashboard.router,            prefix=f"{ADMIN}/dashboard",      tags=["Admin - Dashboard"])
app.include_router(admin_orders.router,         prefix=f"{ADMIN}/orders",         tags=["Admin - Orders"])
app.include_router(admin_products.router,       prefix=f"{ADMIN}/products",       tags=["Admin - Products"])
app.include_router(admin_categories.router,     prefix=f"{ADMIN}/categories",     tags=["Admin - Categories"])
app.include_router(inventory.router,            prefix=f"{ADMIN}/inventory",      tags=["Admin - Inventory"])
app.include_router(admin_coupons.router,        prefix=f"{ADMIN}/coupons",        tags=["Admin - Coupons"])
app.include_router(admin_custom_orders.router,  prefix=f"{ADMIN}/custom-orders",  tags=["Admin - Custom Orders"])
app.include_router(analytics.router,            prefix=f"{ADMIN}/analytics",      tags=["Admin - Analytics"])
app.include_router(staff.router,                prefix=f"{ADMIN}/staff",          tags=["Admin - Staff"])
app.include_router(attendance.router,           prefix=f"{ADMIN}/attendance",     tags=["Admin - Attendance"])
app.include_router(salary.router,               prefix=f"{ADMIN}/salary",         tags=["Admin - Salary"])
app.include_router(customers.router,            prefix=f"{ADMIN}/customers",      tags=["Admin - Customers"])
app.include_router(admin_notifications.router,  prefix=f"{ADMIN}/notifications",  tags=["Admin - Notifications"])
