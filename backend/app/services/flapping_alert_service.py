from sqlalchemy.orm import Session

from app.models.alert import AlertSeverity
from app.repositories.alert_repository import AlertRepository
from app.repositories.device_metric_repository import (
    DeviceMetricRepository,
)


class FlappingAlertService:

    @staticmethod
    def create_flapping_alert_if_needed(
        db: Session,
        device_id: int,
        device_name: str,
    ):
        metrics = (
            DeviceMetricRepository.get_latest_status_metrics(
                db=db,
                device_id=device_id,
                limit=6,
            )
        )

        if len(metrics) < 6:
            return None

        statuses = [
            metric.status
            for metric in reversed(metrics)
        ]

        transitions = 0

        for i in range(len(statuses) - 1):
            if statuses[i] != statuses[i + 1]:
                transitions += 1

        if transitions < 3:
            return None

        active_alert = (
            AlertRepository.get_active_alert_for_device(
                db=db,
                device_id=device_id,
            )
        )

        if active_alert:
            return active_alert

        return AlertRepository.create(
            db=db,
            device_id=device_id,
            severity=AlertSeverity.WARNING,
            message=f"Device flapping detected on {device_name}",
        )