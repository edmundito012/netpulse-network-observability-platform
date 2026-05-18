from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.device import DeviceStatus


class DeviceMetricRead(BaseModel):
    id: int
    device_id: int
    status: DeviceStatus
    response_time_ms: float | None
    checked_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )