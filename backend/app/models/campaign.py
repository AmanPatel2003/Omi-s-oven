from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CampaignModel(BaseModel):
    type: str                       # "targeted" | "broadcast"
    channel: str                     # "email" | "sms" | "whatsapp"
    subject: Optional[str] = None    # email only
    message: str
    segment: Optional[dict] = None   # filter criteria used, for audit — None if targeted by explicit ids
    target_count: int
    sent_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0           # customers who opted out via notification_preferences
    status: str = "queued"           # queued | in_progress | completed | failed
    sent_by: str                     # admin user_id
    created_at: datetime
    completed_at: Optional[datetime] = None