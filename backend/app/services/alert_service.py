from sqlalchemy.orm import Session

from app.models.alert import AlertSeverity
from app.models.device_event import DeviceEventType
from app.repositories.alert_repository import AlertRepository
from app.repositories.device_event_repository import DeviceEventRepository


class AlertService:

    @staticmethod
    def create_packet_loss_alert_if_needed(
        db: Session,
        device_id: int,
        device_name: str,
        packet_loss_percent: float | None,
    ):
        if packet_loss_percent is None:
            return None

        severity = None

        if packet_loss_percent > 20:
            severity = AlertSeverity.CRITICAL

        elif packet_loss_percent > 5:
            severity = AlertSeverity.WARNING

        if severity is None:
            return None

        active_alert = AlertRepository.get_active_alert_for_device(
            db=db,
            device_id=device_id,
        )

        if active_alert:
            return active_alert

        alert = AlertRepository.create(
            db=db,
            device_id=device_id,
            severity=severity,
            message=(
                f"Packet loss detected on {device_name}: "
                f"{packet_loss_percent:.2f}%"
            ),
        )

        DeviceEventRepository.create(
            db=db,
            device_id=device_id,
            event_type=DeviceEventType.ALERT_CREATED,
            message=f"{severity.value} alert created: {alert.message}",
        )

        return alert