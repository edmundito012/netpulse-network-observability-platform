from sqlalchemy.orm import Session

from app.models.device import DeviceStatus
from app.models.device_metric import DeviceMetric


class DeviceMetricRepository:

    @staticmethod
    def create(
        db: Session,
        device_id: int,
        status: DeviceStatus,
        response_time_ms: float | None
    ):
        metric = DeviceMetric(
            device_id=device_id,
            status=status,
            response_time_ms=response_time_ms
        )

        db.add(metric)
        db.commit()
        db.refresh(metric)

        return metric

    @staticmethod
    def get_by_device_id(
        db: Session,
        device_id: int,
        limit: int = 50
    ):
        return (
            db.query(DeviceMetric)
            .filter(DeviceMetric.device_id == device_id)
            .order_by(DeviceMetric.checked_at.desc())
            .limit(limit)
            .all()
        )