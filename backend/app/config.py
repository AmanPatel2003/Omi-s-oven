from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any, ClassVar, Dict, List

class Settings(BaseSettings):
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    
    # SHOP BRANDING
    SHOP_NAME: str = "Sweet Bites"
    SHOP_TAGLINE: str = "Freshly Baked with Love"
    SHOP_PHONE: str = "9876543210"
    SHOP_EMAIL: str = "hello@sweetbites.in"
    SHOP_ADDRESS: str = "42 Palasia Square, AB Road"
    SHOP_CITY: str = "Indore"
    SHOP_TIMEZONE: str = "Asia/Kolkata"

    # App
    APP_NAME: str = "Cake Shop API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # Database
    MONGO_URI: str
    MONGO_DB_NAME: str = "cakeshop"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 360
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Razorpay
    # RAZORPAY_KEY_ID: str
    # RAZORPAY_KEY_SECRET: str
    # RAZORPAY_WEBHOOK_SECRET: str
    

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    CLOUDINARY_FOLDER: str = "cakeshop"

    # Google
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_MAPS_API_KEY: str = ""

    # # Twilio (WhatsApp)
    # TWILIO_ACCOUNT_SID: str = ""
    # TWILIO_AUTH_TOKEN: str = ""
    # TWILIO_WHATSAPP_FROM: str = "whatsapp:+14155238886"

    # # SendGrid
    # SENDGRID_API_KEY: str = ""
    # EMAIL_FROM: str = "noreply@cakeshop.com"

    # # MSG91 (SMS)
    # MSG91_API_KEY: str = ""
    # MSG91_SENDER_ID: str = "CAKSHP"
    
    # SMTP_HOST: str = "smtp.gmail.com"
    # SMTP_PORT: int = 587
    # SMTP_USER: str = "amanpatel22012003@gmail.com"
    # SMTP_PASS: str = "knjp jvmp mkjn mdf"
    # EMAIL_FROM: str = "amanpatel22012003@gmail.com"
    
    # ── EMAIL (Brevo, free tier: 300/day) — ACTIVE ────────────────────
    EMAIL_ENABLED: bool = True
    BREVO_API_KEY: str
    BREVO_FROM_EMAIL: str        # must be a verified sender in your Brevo account
    BREVO_FROM_NAME: str = "Your Bakery Name"

    # ── SMS / WHATSAPP (Twilio) — INACTIVE until you flip these ───────
    SMS_ENABLED: bool = False
    WHATSAPP_ENABLED: bool = False
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_SMS_FROM: str = ""
    TWILIO_WHATSAPP_FROM: str = ""

    # Business config
    DELIVERY_RADIUS_KM: int = 10
    MIN_ORDER_AMOUNT: int = 200
    DELIVERY_FEE: int = 40
    FREE_DELIVERY_ABOVE: int = 500
    REWARD_POINTS_PER_RUPEE: float = 1.0   # 1 point per ₹1 spent
    REWARD_REDEMPTION_RATE: float = 0.25   # 1 point = ₹0.25
    
    
    POINTS_TO_RUPEE_RATE : int= 1          # 1 point = ₹1 discount
    POINTS_EARN_RATE : float = 0.02           # earn 2% of order total (after discount) as points
    MIN_REDEEM_POINTS : int = 100           # can't redeem below this threshold
    MAX_REDEEM_PERCENT_OF_ORDER : float = 0.5 # can't wipe out more than 50% of order value with points

    TIERS: ClassVar[List[Dict[str, Any]]] = [
        {"name": "Silver",   "min_lifetime_points": 0,    "benefits": ["Standard delivery", "Birthday coupon"]},
        {"name": "Gold",     "min_lifetime_points": 1000, "benefits": ["Free delivery over ₹500", "Early access to sales", "1.5x points on orders"]},
        {"name": "Platinum", "min_lifetime_points": 5000, "benefits": ["Free delivery always", "Priority custom orders", "2x points on orders", "Dedicated support"]},
    ]

   

settings = Settings()
