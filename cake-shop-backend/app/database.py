from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client: AsyncIOMotorClient = None
db = None

async def connect_db():
    global client, db
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB_NAME]
    await create_indexes(db)
    print(f"✅ Connected to MongoDB: {settings.MONGO_DB_NAME}")

async def disconnect_db():
    global client
    if client:
        client.close()
        print("❌ Disconnected from MongoDB")

async def get_db():
    return db

async def create_indexes(db):
    # Users
    await db.users.create_index("email", unique=True)
    await db.users.create_index("phone", unique=True)

    # Products
    await db.products.create_index("slug", unique=True)
    await db.products.create_index("category_id")
    await db.products.create_index("is_available")
    await db.products.create_index("total_sold")
    await db.products.create_index([("name", "text"), ("description", "text")])

    # Orders
    await db.orders.create_index("user_id")
    await db.orders.create_index("order_number", unique=True)
    await db.orders.create_index("status")
    await db.orders.create_index("created_at")
    await db.orders.create_index("payment_status")

    # Carts — one per user
    await db.carts.create_index("user_id", unique=True)

    # Rewards — one per user
    await db.rewards.create_index("user_id", unique=True)

    # Coupons
    await db.coupons.create_index("code", unique=True)
    await db.coupons.create_index("valid_until")

    # Attendance — one per staff per day
    await db.attendance.create_index(
        [("staff_id", 1), ("date", 1)], unique=True
    )

    # Payments
    await db.payments.create_index("razorpay_order_id", unique=True)
    await db.payments.create_index("order_id")

    # Inventory
    await db.inventory.create_index("ingredient_name", unique=True)

    # Deliveries
    await db.deliveries.create_index("order_id", unique=True)
    await db.deliveries.create_index("staff_id")
    
    await db.attendance.create_index([("staff_id", 1), ("date", 1)], unique=True)

    print("✅ Database indexes created")
