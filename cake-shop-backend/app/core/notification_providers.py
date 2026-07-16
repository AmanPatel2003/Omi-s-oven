"""
Provider abstraction for outbound email/SMS/WhatsApp.
Every function here is currently a STUB — it logs what it would have sent
and returns success without actually dispatching anything.

To go live:
- Email: wire in SendGrid/SES/Postmark (pip install sendgrid, or boto3 for SES)
- SMS/WhatsApp: wire in Twilio/MSG91/Gupshup (pip install twilio, or use their HTTP API)

Until then, this lets the rest of the admin panel, batching logic, and
delivery tracking work end-to-end and be tested — only the final external
API call is missing.
"""
from app.config import settings


async def send_email(to: str, subject: str, body: str) -> dict:
    # STUB — replace with real provider call
    print(f"[STUB EMAIL] to={to} subject={subject}")
    return {"success": False, "error": "Email provider not configured"}


async def send_sms(to: str, message: str) -> dict:
    # STUB — replace with real provider call
    print(f"[STUB SMS] to={to} message={message[:50]}")
    return {"success": False, "error": "SMS provider not configured"}


async def send_whatsapp(to: str, message: str) -> dict:
    # STUB — replace with real provider call
    print(f"[STUB WHATSAPP] to={to} message={message[:50]}")
    return {"success": False, "error": "WhatsApp provider not configured"}


PROVIDER_MAP = {
    "email": send_email,
    "sms": send_sms,
    "whatsapp": send_whatsapp,
}