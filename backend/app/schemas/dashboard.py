from pydantic import BaseModel

from app.schemas.device_event import DeviceEventRead


class DashboardOverviewRead(BaseModel):
    total_devices: int
    online_devices: int
    offline_devices: int
    unknown_devices: int

    open_alerts: int
    acknowledged_alerts: int
    resolved_alerts: int

    critical_alerts: int
    warning_alerts: int
    info_alerts: int

    latest_events: list[DeviceEventRead]