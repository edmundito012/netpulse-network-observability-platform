from datetime import datetime

from pydantic import BaseModel


class DeviceSNMPSystemSnapshotRead(BaseModel):
    id: int
    device_id: int
    sysdescr: str | None
    sysuptime: str | None
    syscontact: str | None
    sysname: str | None
    syslocation: str | None
    collected_at: datetime

    class Config:
        from_attributes = True