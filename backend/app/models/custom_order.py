from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CustomOrderModel(BaseModel):
    request_number: str          # e.g. "CO-20260714-0001"
    user_id: str

    occasion: str                 # birthday, wedding, anniversary, other
    flavor: str
    size: str                     # e.g. "1kg", "2kg", "3-tier"
    shape: Optional[str] = None
    message_on_cake: Optional[str] = None
    reference_images: list[str] = Field(default_factory=list)
    description: str              # free-text details of what they want
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    needed_by: datetime           # date they need it delivered/ready by

    contact_phone: str
    delivery_address_id: Optional[str] = None   # None if store pickup

    status: str = "pending"       # pending -> reviewing -> quoted -> confirmed -> in_progress -> completed | rejected | cancelled
    quoted_price: Optional[float] = None
    admin_note: Optional[str] = None

    status_history: list[dict] = Field(default_factory=list)

    created_at: datetime
    updated_at: datetime