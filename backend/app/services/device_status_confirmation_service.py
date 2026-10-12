from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.device import DeviceStatus
from app.repositories.device_metric_repository import DeviceMetricRepository


class DeviceStatusConfirmationService:
    """Confirm device transitions from persisted ping observations."""

    @staticmethod
    def confirm(
        db: Session,
        device_id: int,
        current_status: DeviceStatus,
        observed_status: DeviceStatus,
    ) -> DeviceStatus:
        if observed_status == current_status:
            return current_status

        if observed_status == DeviceStatus.OFFLINE:
            required_cycles = settings.OFFLINE_CONFIRMATION_CYCLES
        elif observed_status == DeviceStatus.ONLINE:
            required_cycles = settings.ONLINE_CONFIRMATION_CYCLES
        else:
            return current_status

        metrics = DeviceMetricRepository.get_latest_status_metrics(
            db=db,
            device_id=device_id,
            limit=required_cycles,
        )

        if len(metrics) < required_cycles:
            return current_status

        if all(
            metric.status == observed_status for metric in metrics[:required_cycles]
        ):
            return observed_status

        return current_status
