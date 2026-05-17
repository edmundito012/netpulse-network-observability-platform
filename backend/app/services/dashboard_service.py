from sqlalchemy.orm import Session

from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.models.device import Device, DeviceStatus
from app.repositories.device_event_repository import DeviceEventRepository


class DashboardService:

    @staticmethod
    def get_overview(db: Session):
        total_devices = db.query(Device).count()

        online_devices = (
            db.query(Device)
            .filter(Device.status == DeviceStatus.ONLINE)
            .count()
        )

        offline_devices = (
            db.query(Device)
            .filter(Device.status == DeviceStatus.OFFLINE)
            .count()
        )

        unknown_devices = (
            db.query(Device)
            .filter(Device.status == DeviceStatus.UNKNOWN)
            .count()
        )

        open_alerts = (
            db.query(Alert)
            .filter(Alert.status == AlertStatus.OPEN)
            .count()
        )

        acknowledged_alerts = (
            db.query(Alert)
            .filter(Alert.status == AlertStatus.ACKNOWLEDGED)
            .count()
        )

        resolved_alerts = (
            db.query(Alert)
            .filter(Alert.status == AlertStatus.RESOLVED)
            .count()
        )

        critical_alerts = (
            db.query(Alert)
            .filter(Alert.severity == AlertSeverity.CRITICAL)
            .count()
        )

        warning_alerts = (
            db.query(Alert)
            .filter(Alert.severity == AlertSeverity.WARNING)
            .count()
        )

        info_alerts = (
            db.query(Alert)
            .filter(Alert.severity == AlertSeverity.INFO)
            .count()
        )

        latest_events = DeviceEventRepository.get_all(
            db=db,
            limit=10,
        )

        return {
            "total_devices": total_devices,
            "online_devices": online_devices,
            "offline_devices": offline_devices,
            "unknown_devices": unknown_devices,
            "open_alerts": open_alerts,
            "acknowledged_alerts": acknowledged_alerts,
            "resolved_alerts": resolved_alerts,
            "critical_alerts": critical_alerts,
            "warning_alerts": warning_alerts,
            "info_alerts": info_alerts,
            "latest_events": latest_events,
        }