from pydantic import BaseModel

from app.schemas.alert import AlertRead
from app.schemas.device import DeviceRead
from app.schemas.device_event import DeviceEventRead
from app.schemas.device_metric import DeviceMetricRead
from app.schemas.device_snmp_system_snapshot import (
    DeviceSNMPSystemSnapshotRead,
)


class DeviceSummaryRead(BaseModel):
    device: DeviceRead
    latest_metric: DeviceMetricRead | None = None
    latest_snmp_snapshot: DeviceSNMPSystemSnapshotRead | None = None
    active_alert: AlertRead | None = None
    recent_events: list[DeviceEventRead]