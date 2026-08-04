"""
Provider layer for outbound email/SMS/WhatsApp.

- Email (Brevo, free tier): ACTIVE by default (EMAIL_ENABLED=true in .env).
- SMS and WhatsApp (Twilio): fully implemented but INACTIVE until you set
  SMS_ENABLED=true / WHATSAPP_ENABLED=true and fill in Twilio credentials
  in .env. No code changes needed to activate later.
"""
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from twilio.rest import Client as TwilioClient

from app.config import settings

_brevo_config = sib_api_v3_sdk.Configuration()
_brevo_config.api_key["api-key"] = settings.BREVO_API_KEY
_brevo_client = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(_brevo_config)) if settings.BREVO_API_KEY else None

_twilio_client = (
    TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN
    else None
)


# ── EMAIL — ACTIVE ──────────────────────────────────────────────────
async def send_email(to: str, subject: str, body: str) -> dict:
    if not settings.EMAIL_ENABLED:
        return {"success": False, "error": "Email sending is disabled (EMAIL_ENABLED=false)"}

    if not _brevo_client:
        return {"success": False, "error": "BREVO_API_KEY is not configured"}

    try:
        email = sib_api_v3_sdk.SendSmtpEmail(
            sender={"email": settings.BREVO_FROM_EMAIL, "name": settings.BREVO_FROM_NAME},
            to=[{"email": to}],
            subject=subject,
            text_content=body,
        )
        response = _brevo_client.send_transac_email(email)
        return {"success": True, "message_id": response.message_id}
    except ApiException as e:
        return {"success": False, "error": f"Brevo error: {e.reason} (status {e.status})"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def send_email_with_attachment(to: str, subject: str, body: str, pdf_bytes: bytes, filename: str) -> dict:
    """Used for salary slips — Brevo attachments need base64-encoded content."""
    if not settings.EMAIL_ENABLED:
        return {"success": False, "error": "Email sending is disabled (EMAIL_ENABLED=false)"}

    if not _brevo_client:
        return {"success": False, "error": "BREVO_API_KEY is not configured"}

    import base64
    try:
        email = sib_api_v3_sdk.SendSmtpEmail(
            sender={"email": settings.BREVO_FROM_EMAIL, "name": settings.BREVO_FROM_NAME},
            to=[{"email": to}],
            subject=subject,
            text_content=body,
            attachment=[{"content": base64.b64encode(pdf_bytes).decode(), "name": filename}],
        )
        response = _brevo_client.send_transac_email(email)
        return {"success": True, "message_id": response.message_id}
    except ApiException as e:
        return {"success": False, "error": f"Brevo error: {e.reason} (status {e.status})"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── SMS — INACTIVE (SMS_ENABLED=false by default) ────────────────────
async def send_sms(to: str, message: str) -> dict:
    if not settings.SMS_ENABLED:
        return {"success": False, "error": "SMS sending is disabled (SMS_ENABLED=false)"}

    if not _twilio_client or not settings.TWILIO_SMS_FROM:
        return {"success": False, "error": "Twilio SMS credentials are not configured"}

    try:
        result = _twilio_client.messages.create(
            body=message,
            from_=settings.TWILIO_SMS_FROM,
            to=to if to.startswith("+") else f"+91{to}",
        )
        return {"success": True, "sid": result.sid}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── WHATSAPP — INACTIVE (WHATSAPP_ENABLED=false by default) ─────────
async def send_whatsapp(to: str, message: str) -> dict:
    if not settings.WHATSAPP_ENABLED:
        return {"success": False, "error": "WhatsApp sending is disabled (WHATSAPP_ENABLED=false)"}

    if not _twilio_client or not settings.TWILIO_WHATSAPP_FROM:
        return {"success": False, "error": "Twilio WhatsApp credentials are not configured"}

    try:
        to_number = to if to.startswith("+") else f"+91{to}"
        result = _twilio_client.messages.create(
            body=message,
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{to_number}",
        )
        return {"success": True, "sid": result.sid}
    except Exception as e:
        return {"success": False, "error": str(e)}


PROVIDER_MAP = {
    "email": send_email,
    "sms": send_sms,
    "whatsapp": send_whatsapp,
}