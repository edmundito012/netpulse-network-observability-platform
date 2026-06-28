from datetime import datetime

from pydantic import BaseModel


class NotificationLogRead(BaseModel):
    id: int
    provider: str
    title: str
    status: str
    sent_at: datetime

    class Config:
        from_attributes = True