# GET    /notifications              My notification history
# PUT    /notifications/:id/read     Mark one as read
# PUT    /notifications/read-all     Mark all as read
# PUT    /notifications/preferences  Toggle email/SMS/WhatsApp preferences

from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.common import SuccessResponse
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    NotificationPreferences,
    UpdatePreferencesRequest,
)
from app.services import notification_service
from app.utils.helpers import success_response

router = APIRouter()


# ── STATIC ROUTES FIRST — read-all and preferences before {id}/read ──

@router.put("/read-all")
async def mark_all_read(current_user=Depends(get_current_user), db=Depends(get_db)):
    result = await notification_service.mark_all_as_read(db=db, user_id=current_user["_id"])
    return success_response(data=result, message="All notifications marked as read")


@router.get("/preferences", response_model=SuccessResponse[NotificationPreferences])
async def get_preferences(current_user=Depends(get_current_user), db=Depends(get_db)):
    result = await notification_service.get_preferences(db=db, user_id=current_user["_id"])
    return success_response(data=result)


@router.put("/preferences", response_model=SuccessResponse[NotificationPreferences])
async def update_preferences(
    body: UpdatePreferencesRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await notification_service.update_preferences(
        db=db,
        user_id=current_user["_id"],
        email=body.email,
        sms=body.sms,
        whatsapp=body.whatsapp,
    )
    return success_response(data=result, message="Preferences updated")


# ── LIST ────────────────────────────────────────────────────────────

@router.get("", response_model=SuccessResponse[NotificationListResponse])
async def list_notifications(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await notification_service.list_notifications(db=db, user_id=current_user["_id"], page=page, limit=limit)
    return success_response(data=result)


# ── MARK ONE READ — dynamic {id} route last ───────────────────────

@router.put("/{notification_id}/read", response_model=SuccessResponse[NotificationResponse])
async def mark_read(
    notification_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await notification_service.mark_as_read(db=db, user_id=current_user["_id"], notification_id=notification_id)
    return success_response(data=result, message="Notification marked as read")