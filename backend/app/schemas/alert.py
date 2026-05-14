from datetime import datetime
from pydantic import BaseModel

from app.models.alert import AlertSeverity, AlertStatus


class AlertRead(BaseModel):
    id: int
    device_id: int
    severity: AlertSeverity
    status: AlertStatus
    message: str
    created_at: datetime
    resolved_at: datetime | None = None

    class Config:
        from_attributes = True