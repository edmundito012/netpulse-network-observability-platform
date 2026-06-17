from pydantic import BaseModel
from typing import Optional

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

    predictive_alerts: int
    devices_with_predictive_risk: int

    network_health_score: int

    devices_at_risk: int
    highest_risk_device: Optional[dict]

    latest_events: list[DeviceEventRead]