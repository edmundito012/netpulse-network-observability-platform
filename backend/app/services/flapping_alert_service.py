"""Device flapping alert service."""

from sqlalchemy.orm import Session

from app.models.alert import (
    AlertSeverity,
    AlertType,
)
from app.repositories.device_metric_repository import (
    DeviceMetricRepository,
)
from app.services.alert_deduplication_service import (
    AlertDeduplicationService,
)


class FlappingAlertService:
    """Detect repeated device status transitions."""

    @staticmethod
    def create_flapping_alert_if_needed(
        db: Session,
        device_id: int,
        device_name: str,
    ):
        metrics = (
            DeviceMetricRepository
            .get_latest_status_metrics(
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

        transitions = sum(
            1
            for index in range(
                len(statuses) - 1
            )
            if (
                statuses[index]
                != statuses[index + 1]
            )
        )

        if transitions < 3:
            return None

        result = (
            AlertDeduplicationService
            .create_or_update(
                db=db,
                device_id=device_id,
                alert_type=AlertType.FLAPPING,
                severity=AlertSeverity.WARNING,
                message=(
                    f"Device flapping detected "
                    f"on {device_name}"
                ),
            )
        )

        return result.alert