"""Device availability alert lifecycle service."""

from sqlalchemy.orm import Session

from app.models.alert import (
    Alert,
    AlertSeverity,
    AlertType,
)
from app.models.device import DeviceStatus
from app.models.device_event import DeviceEventType
from app.repositories.alert_repository import AlertRepository
from app.repositories.device_event_repository import (
    DeviceEventRepository,
)
from app.services.alert_deduplication_service import (
    AlertDeduplicationService,
)


class DeviceAvailabilityAlertService:
    """Keep the device-offline alert aligned with reachability."""

    @classmethod
    def reconcile(
        cls,
        db: Session,
        *,
        device_id: int,
        device_name: str,
        status: DeviceStatus,
    ) -> Alert | None:
        """Open or resolve the availability alert for a device."""

        if status == DeviceStatus.OFFLINE:
            return cls._open_or_update(
                db=db,
                device_id=device_id,
                device_name=device_name,
            )

        if status == DeviceStatus.ONLINE:
            return cls._resolve_if_active(
                db=db,
                device_id=device_id,
            )

        return None

    @staticmethod
    def _open_or_update(
        db: Session,
        *,
        device_id: int,
        device_name: str,
    ) -> Alert:
        result = AlertDeduplicationService.create_or_update(
            db=db,
            device_id=device_id,
            alert_type=AlertType.DEVICE_OFFLINE,
            severity=AlertSeverity.CRITICAL,
            message=f"Device {device_name} is offline",
        )

        if result.created:
            DeviceEventRepository.create(
                db=db,
                device_id=device_id,
                event_type=DeviceEventType.ALERT_CREATED,
                message=f"Critical alert created: {result.alert.message}",
            )

        return result.alert

    @staticmethod
    def _resolve_if_active(
        db: Session,
        *,
        device_id: int,
    ) -> Alert | None:
        deduplication_key = AlertDeduplicationService.build_deduplication_key(
            device_id=device_id,
            alert_type=AlertType.DEVICE_OFFLINE,
        )

        active_alert = AlertRepository.get_active_by_deduplication_key(
            db=db,
            device_id=device_id,
            deduplication_key=deduplication_key,
        )

        if active_alert is None:
            return None

        resolved_alert = AlertRepository.resolve(
            db=db,
            alert=active_alert,
        )

        DeviceEventRepository.create(
            db=db,
            device_id=device_id,
            event_type=DeviceEventType.ALERT_RESOLVED,
            message=f"Alert resolved: {resolved_alert.message}",
        )

        return resolved_alert
