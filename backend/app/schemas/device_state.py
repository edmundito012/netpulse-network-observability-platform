from datetime import datetime

from pydantic import BaseModel


class DeviceStateRead(BaseModel):
    device_id: int
    device_name: str
    ip_address: str
    status: str
    response_time_ms: float | None = None
    last_checked_at: datetime
