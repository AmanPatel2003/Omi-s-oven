# POST   /admin/notifications/send        Send manual WhatsApp/SMS/email blast
# POST   /admin/notifications/broadcast   Send announcement to all customers

from fastapi import APIRouter, Depends

from app.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.common import SuccessResponse
from app.schemas.admin_notification import (
    SendNotificationRequest,
    BroadcastRequest,
    CampaignResponse,
)
from app.services import admin_notification_service
from app.utils.helpers import success_response

router = APIRouter(dependencies=[Depends(get_current_admin)])


@router.post("/send", response_model=SuccessResponse[CampaignResponse])
async def send_notification(
    body: SendNotificationRequest,
    current_admin=Depends(get_current_admin),
    db=Depends(get_db),
):
    result = await admin_notification_service.send_notification(
        db=db,
        admin_id=current_admin["_id"],
        channel=body.channel,
        customer_ids=body.customer_ids,
        segment=body.segment.model_dump() if body.segment else None,
        subject=body.subject,
        message=body.message,
    )
    message = "Campaign sent" if result["provider_configured"] else "Campaign logged (provider not configured)"
    return success_response(data=result, message=message)


@router.post("/broadcast", response_model=SuccessResponse[CampaignResponse])
async def broadcast_notification(
    body: BroadcastRequest,
    current_admin=Depends(get_current_admin),
    db=Depends(get_db),
):
    result = await admin_notification_service.broadcast_notification(
        db=db,
        admin_id=current_admin["_id"],
        channel=body.channel,
        subject=body.subject,
        message=body.message,
        exclude_inactive=body.exclude_inactive,
    )
    message = "Broadcast sent" if result["provider_configured"] else "Broadcast logged (provider not configured)"
    return success_response(data=result, message=message)