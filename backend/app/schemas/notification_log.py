"""Pydantic schemas for notification history responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationLogRead(BaseModel):
    """Notification delivery history response."""

    id: int
    provider: str
    title: str
    status: str
    sent_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )