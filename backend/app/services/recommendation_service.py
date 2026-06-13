from sqlalchemy.orm import Session

from app.repositories.alert_repository import AlertRepository
from app.repositories.device_metric_repository import DeviceMetricRepository


class RecommendationService:

    @staticmethod
    def generate(
        db: Session,
        device,
    ) -> str:
        metrics = DeviceMetricRepository.get_latest_metrics(
            db=db,
            device_id=device.id,
            limit=5,
        )

        active_alert = AlertRepository.get_active_alert_for_device(
            db=db,
            device_id=device.id,
        )

        if not metrics:
            return "No metrics available yet. Run a device check first."

        latest_metric = metrics[0]

        packet_loss = latest_metric.packet_loss_percent or 0
        latency = latest_metric.response_time_ms or 0

        if packet_loss > 20:
            return (
                "Critical packet loss detected. Check WAN connectivity, "
                "upstream provider, cables, or interface errors."
            )

        if packet_loss > 5:
            return (
                "Packet loss detected. Monitor the link and verify interface "
                "stability before users are impacted."
            )

        if latency > 100:
            return (
                "High latency detected. Investigate congestion, routing path, "
                "or overloaded network devices."
            )

        if latency > 50:
            return (
                "Moderate latency increase detected. Continue monitoring and "
                "compare with baseline performance."
            )

        if active_alert:
            return (
                "Active alert exists. Review the alert timeline and recent "
                "device events for root cause."
            )

        return "Device appears healthy. No immediate action required."