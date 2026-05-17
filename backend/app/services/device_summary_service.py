from sqlalchemy.orm import Session

from app.repositories.alert_repository import AlertRepository
from app.repositories.device_event_repository import (
    DeviceEventRepository,
)
from app.repositories.device_metric_repository import (
    DeviceMetricRepository,
)
from app.repositories.device_repository import DeviceRepository
from app.repositories.device_snmp_system_snapshot_repository import (
    DeviceSNMPSystemSnapshotRepository,
)


class DeviceSummaryService:

    @staticmethod
    def get_summary(
        db: Session,
        device_id: int,
    ):
        device = DeviceRepository.get_by_id(
            db=db,
            device_id=device_id,
        )

        if not device:
            return None

        latest_metric = (
            DeviceMetricRepository.get_latest_by_device(
                db=db,
                device_id=device_id,
            )
        )

        latest_snmp_snapshot = (
            DeviceSNMPSystemSnapshotRepository.get_latest_by_device(
                db=db,
                device_id=device_id,
            )
        )

        active_alert = (
            AlertRepository.get_active_alert_for_device(
                db=db,
                device_id=device_id,
            )
        )

        recent_events = (
            DeviceEventRepository.get_by_device(
                db=db,
                device_id=device_id,
                limit=10,
            )
        )

        return {
            "device": device,
            "latest_metric": latest_metric,
            "latest_snmp_snapshot": latest_snmp_snapshot,
            "active_alert": active_alert,
            "recent_events": recent_events,
        }