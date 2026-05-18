from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.device_event import DeviceEventType


class DeviceEventRead(BaseModel):
    id: int
    device_id: int
    event_type: DeviceEventType
    message: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )