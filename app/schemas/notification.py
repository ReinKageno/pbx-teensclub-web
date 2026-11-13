
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import NotifyType


class NotificationBase(BaseModel):
    type: NotifyType
    message: str
    link: str | None = False
    is_admin_only: bool = False

class NotificationCreate(NotificationBase):
    announcement: bool = False
    pass

class NotificationUpdate(NotificationBase):
    pass

class NotificationSchema(NotificationBase):
    id: str
    created_at: datetime
    is_read: bool = False

    model_config = ConfigDict(from_attributes=True)

class NotificationStatusSchema(BaseModel):
    id: str
    type: NotifyType
    is_admin_only: bool = False
    created_at: datetime
    is_read: bool = False