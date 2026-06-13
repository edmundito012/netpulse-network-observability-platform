from sqlalchemy.orm import Session

from app.models.alert import AlertSeverity
from app.repositories.alert_repository import AlertRepository
from app.repositories.device_metric_repository import (
    DeviceMetricRepository,
)


class LatencyAlertService:

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
            latencies[i] < latencies[i + 1]
            for i in range(len(latencies) - 1)
        )

        if not is_increasing:
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
            message=(
                f"Latency degradation detected "
                f"on {device_name}"
            ),
        )