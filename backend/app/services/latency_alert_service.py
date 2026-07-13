"""Latency trend alert service."""

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


class LatencyAlertService:
    """Detect monotonically increasing latency degradation."""

    @staticmethod
    def create_latency_trend_alert_if_needed(
        db: Session,
        device_id: int,
        device_name: str,
    ):
        metrics = (
            DeviceMetricRepository.get_latest_metrics(
                db=db,
                device_id=device_id,
                limit=5,
            )
        )

        if len(metrics) < 5:
            return None

        latencies = [
            metric.response_time_ms
            for metric in reversed(metrics)
            if metric.response_time_ms is not None
        ]

        if len(latencies) < 5:
            return None

        is_increasing = all(
            latencies[index]
            < latencies[index + 1]
            for index in range(
                len(latencies) - 1
            )
        )

        if not is_increasing:
            return None

        result = (
            AlertDeduplicationService
            .create_or_update(
                db=db,
                device_id=device_id,
                alert_type=AlertType.LATENCY_TREND,
                severity=AlertSeverity.WARNING,
                message=(
                    "Latency degradation detected "
                    f"on {device_name}"
                ),
            )
        )

        return result.alert