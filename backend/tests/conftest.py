"""
Shared pytest fixtures for the entire test suite.

Design decisions:
- Uses mongomock-motor (or a real disposable Mongo test DB — swap MONGO_TEST_URI
  if you prefer hitting a real local Mongo instance instead of an in-memory mock).
- Every external paid service (Razorpay, Cloudinary, SMS/Email providers) is
  mocked at the module level — tests must NEVER hit real third-party APIs.
- Auth fixtures pre-create users of each role (customer, admin, super_admin,
  delivery_staff) and return ready-to-use Bearer tokens, so individual test
  files don't repeat registration boilerplate.

Install:
    pip install pytest pytest-asyncio httpx mongomock-motor --break-system-packages
"""
import asyncio
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from app.main import app
from app.database import get_db
from app.core.security import hash_password, create_access_token


# ── EVENT LOOP ──────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── TEST DATABASE (in-memory Mongo mock, isolated per test) ──────────
@pytest_asyncio.fixture
async def db():
    from mongomock_motor import AsyncMongoMockClient
    client = AsyncMongoMockClient()
    test_db = client["test_db"]

    # required unique indexes — mirrors production create_indexes()
    await test_db.users.create_index("email", unique=True)
    await test_db.users.create_index("phone", unique=True)
    await test_db.products.create_index("slug", unique=True)
    await test_db.categories.create_index("slug", unique=True)
    await test_db.coupons.create_index("code", unique=True)
    await test_db.attendance.create_index([("staff_id", 1), ("date", 1)], unique=True)

    app.dependency_overrides[get_db] = lambda: test_db
    yield test_db
    app.dependency_overrides.clear()


# ── HTTP CLIENT ───────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def client(db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── MOCK EXTERNAL PROVIDERS ────────────────────────────────────────────
@pytest.fixture(autouse=True)
def mock_razorpay():
    with patch("app.services.payment_service.client") as mock_client:
        mock_client.order.create.return_value = {"id": "order_test123"}
        mock_client.payment.refund.return_value = {"id": "rfnd_test123"}
        yield mock_client


@pytest.fixture(autouse=True)
def mock_cloudinary():
    with patch("app.core.cloudinary_client.cloudinary.uploader.upload") as mock_upload, \
         patch("app.core.cloudinary_client.cloudinary.uploader.destroy") as mock_destroy:
        mock_upload.return_value = {
            "secure_url": "https://res.cloudinary.com/test/image/upload/test.jpg",
            "public_id": "test/test_image",
        }
        mock_destroy.return_value = {"result": "ok"}
        yield mock_upload, mock_destroy


@pytest.fixture(autouse=True)
def mock_notification_providers():
    with patch("app.core.notification_providers.send_email", new_callable=AsyncMock) as mock_email, \
         patch("app.core.notification_providers.send_sms", new_callable=AsyncMock) as mock_sms:
        mock_email.return_value = {"success": True}
        mock_sms.return_value = {"success": True}
        yield mock_email, mock_sms


# ── USER FIXTURES (each creates a real DB user + returns auth headers) ──
async def _create_user(db, role="customer", **overrides):
    now = datetime.utcnow()
    defaults = {
        "name": "Test User",
        "email": f"{role}_{now.timestamp()}@test.com",
        "phone": f"9{str(int(now.timestamp()))[-9:]}",
        "password_hash": hash_password("TestPass123"),
        "role": role,
        "is_active": True,
        "addresses": [],
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    result = await db.users.insert_one(defaults)
    user_id = str(result.inserted_id)

    if role == "customer":
        await db.rewards.insert_one({
            "user_id": user_id, "total_points": 0, "lifetime_points": 0,
            "transactions": [], "created_at": now, "updated_at": now,
        })

    token = create_access_token({"sub": user_id, "role": role})
    return user_id, {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def customer(db):
    user_id, headers = await _create_user(db, role="customer")
    return {"id": user_id, "headers": headers}


@pytest_asyncio.fixture
async def second_customer(db):
    """A distinct customer — needed for IDOR / cross-account access tests."""
    user_id, headers = await _create_user(db, role="customer")
    return {"id": user_id, "headers": headers}


@pytest_asyncio.fixture
async def admin(db):
    user_id, headers = await _create_user(db, role="admin")
    return {"id": user_id, "headers": headers}


@pytest_asyncio.fixture
async def super_admin(db):
    user_id, headers = await _create_user(db, role="super_admin")
    return {"id": user_id, "headers": headers}


@pytest_asyncio.fixture
async def delivery_staff(db):
    user_id, headers = await _create_user(db, role="delivery_staff")
    return {"id": user_id, "headers": headers}


# ── PRODUCT / CATEGORY / COUPON FIXTURES ──────────────────────────────
@pytest_asyncio.fixture
async def category(db):
    now = datetime.utcnow()
    doc = {
        "name": "Cakes", "slug": "cakes", "description": "Fresh cakes",
        "image": None, "sort_order": 1, "is_active": True,
        "created_at": now, "updated_at": now,
    }
    result = await db.categories.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


@pytest_asyncio.fixture
async def product(db, category):
    now = datetime.utcnow()
    doc = {
        "name": "Chocolate Truffle Cake", "slug": "chocolate-truffle-cake",
        "description": "Rich chocolate cake", "category": category["slug"],
        "price": 599.0, "discount_price": None, "images": [], "tags": ["bestseller"],
        "variants": [], "is_eggless": False, "stock": 20, "low_stock_threshold": 5,
        "is_available": True, "is_featured": True,
        "total_sold": 0, "avg_rating": 0.0, "review_count": 0,
        "created_at": now, "updated_at": now,
    }
    result = await db.products.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


@pytest_asyncio.fixture
async def coupon(db):
    now = datetime.utcnow()
    doc = {
        "code": "SAVE20", "description": "20% off", "discount_type": "percentage",
        "discount_value": 20, "max_discount": 200, "min_order_value": 300,
        "usage_limit": 100, "used_count": 0, "is_public": True, "is_active": True,
        "expires_at": now + timedelta(days=30), "created_at": now,
    }
    result = await db.coupons.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


@pytest_asyncio.fixture
async def address(db, customer):
    """Adds a saved address to the customer fixture's user doc, returns its id."""
    from bson import ObjectId
    addr = {
        "_id": "addr_test_1", "full_name": "Test User", "phone": "9876543210",
        "address_line1": "123 Test St", "city": "Jabalpur", "state": "MP",
        "postal_code": "482001", "address_type": "Home", "is_default": True,
        "created_at": datetime.utcnow(), "updated_at": datetime.utcnow(),
    }
    await db.users.update_one(
        {"_id": ObjectId(customer["id"])},
        {"$push": {"addresses": addr}},
    )
    return addr["_id"]
