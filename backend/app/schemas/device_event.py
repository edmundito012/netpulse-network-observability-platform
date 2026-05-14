from datetime import datetime

from pydantic import BaseModel

from app.models.device_event import DeviceEventType


class DeviceEventRead(BaseModel):
    id: int
    device_id: int
    event_type: DeviceEventType
    message: str
    created_at: datetime

    class Config:
        from_attributes = True