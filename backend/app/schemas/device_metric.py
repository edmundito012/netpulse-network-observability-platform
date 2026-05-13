from datetime import datetime

from pydantic import BaseModel

from app.models.device import DeviceStatus


class DeviceMetricRead(BaseModel):
    id: int
    device_id: int
    status: DeviceStatus
    response_time_ms: float | None
    checked_at: datetime

    class Config:
        from_attributes = True