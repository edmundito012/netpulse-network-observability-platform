from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DeviceSNMPSystemSnapshotRead(BaseModel):
    id: int
    device_id: int
    sysdescr: str | None
    sysuptime: str | None
    syscontact: str | None
    sysname: str | None
    syslocation: str | None
    collected_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )