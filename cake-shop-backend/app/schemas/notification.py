from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    reference_id: Optional[str] = None
    is_read: bool
    created_at: datetime


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    unread_count: int
    meta: PaginationMeta


class NotificationPreferences(BaseModel):
    email: bool = True
    sms: bool = True
    whatsapp: bool = False


class UpdatePreferencesRequest(BaseModel):
    email: Optional[bool] = None
    sms: Optional[bool] = None
    whatsapp: Optional[bool] = None