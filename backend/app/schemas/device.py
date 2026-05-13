from datetime import datetime

from pydantic import BaseModel, IPvAnyAddress

from app.models.device import DeviceStatus


class DeviceBase(BaseModel):
    name: str
    ip_address: IPvAnyAddress
    hostname: str | None = None
    device_type: str
    location: str | None = None


class DeviceCreate(DeviceBase):
    status: DeviceStatus = DeviceStatus.UNKNOWN


class DeviceUpdate(BaseModel):
    name: str | None = None
    ip_address: str | None = None
    hostname: str | None = None
    device_type: str | None = None
    location: str | None = None
    status: DeviceStatus | None = None


class DeviceRead(DeviceBase):
    id: int
    status: DeviceStatus
    created_at: datetime

    class Config:
        from_attributes = True