from sqlalchemy.orm import Session

from app.repositories.alert_repository import AlertRepository
from app.repositories.device_metric_repository import DeviceMetricRepository


class HealthScoreService:

    @staticmethod
    def calculate(
        db: Session,
        device,
    ):
        score = 100

        metrics = (
            DeviceMetricRepository.get_latest_metrics(
                db=db,
                device_id=device.id,
                limit=5,
            )
        )

        if metrics:

            latest = metrics[0]

            latency = latest.response_time_ms or 0
            packet_loss = latest.packet_loss_percent or 0

            if latency > 100:
                score -= 20

            elif latency > 50:
                score -= 10

            if packet_loss > 20:
                score -= 25

            elif packet_loss > 5:
                score -= 10

        active_alert = (
            AlertRepository.get_active_alert_for_device(
                db=db,
                device_id=device.id,
            )
        )

        if active_alert:
            score -= 15

        score = max(score, 0)

        if score >= 90:
            status = "EXCELLENT"

        elif score >= 75:
            status = "GOOD"

        elif score >= 50:
            status = "WARNING"

        else:
            status = "CRITICAL"

        return {
            "device_id": device.id,
            "device_name": device.name,
            "score": score,
            "status": status,
        }