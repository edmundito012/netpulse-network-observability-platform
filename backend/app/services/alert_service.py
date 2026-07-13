"""Application service for threshold-based alerts."""

from sqlalchemy.orm import Session

from app.models.alert import (
    AlertSeverity,
    AlertType,
)
from app.models.device_event import DeviceEventType
from app.repositories.device_event_repository import (
    DeviceEventRepository,
)
from app.services.alert_deduplication_service import (
    AlertDeduplicationService,
)


class AlertService:
    """Evaluate threshold alerts and persist them safely."""

    @staticmethod
    def create_packet_loss_alert_if_needed(
        db: Session,
        device_id: int,
        device_name: str,
        packet_loss_percent: float | None,
    ):
        """Create or deduplicate an instantaneous packet loss alert."""

        if packet_loss_percent is None:
            return None

        severity: AlertSeverity | None = None

        if packet_loss_percent > 20:
            severity = AlertSeverity.CRITICAL
        elif packet_loss_percent > 5:
            severity = AlertSeverity.WARNING

        if severity is None:
            return None

        message = (
            f"Packet loss detected on {device_name}: "
            f"{packet_loss_percent:.2f}%"
        )

        result = (
            AlertDeduplicationService
            .create_or_update(
                db=db,
                device_id=device_id,
                alert_type=AlertType.PACKET_LOSS,
                severity=severity,
                message=message,
            )
        )

        if result.created:
            DeviceEventRepository.create(
                db=db,
                device_id=device_id,
                event_type=(
                    DeviceEventType.ALERT_CREATED
                ),
                message=(
                    f"{severity.value} alert created: "
                    f"{result.alert.message}"
                ),
            )

        return result.alert