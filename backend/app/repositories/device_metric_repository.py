from sqlalchemy.orm import Session

from app.models.device import DeviceStatus
from app.models.device_metric import DeviceMetric


class DeviceMetricRepository:

    @staticmethod
    def create(
        db: Session,
        device_id: int,
        status: DeviceStatus,
        response_time_ms: float | None,
    ):
        metric = DeviceMetric(
            device_id=device_id,
            status=status,
            response_time_ms=response_time_ms,
        )

        db.add(metric)
        db.commit()
        db.refresh(metric)

        return metric

    @staticmethod
    def get_by_device_id(
        db: Session,
        device_id: int,
        limit: int = 50,
    ):
        return (
            db.query(DeviceMetric)
            .filter(DeviceMetric.device_id == device_id)
            .order_by(DeviceMetric.checked_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_paginated_by_device_id(
        db: Session,
        device_id: int,
        page: int = 1,
        page_size: int = 20,
    ):
        query = db.query(DeviceMetric).filter(
            DeviceMetric.device_id == device_id
        )

        total_count = query.count()

        items = (
            query
            .order_by(DeviceMetric.checked_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        total_pages = (
            (total_count + page_size - 1) // page_size
            if total_count > 0
            else 0
        )

        return {
            "items": items,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    @staticmethod
    def get_latest_by_device(
        db: Session,
        device_id: int,
    ):
        return (
            db.query(DeviceMetric)
            .filter(DeviceMetric.device_id == device_id)
            .order_by(DeviceMetric.checked_at.desc())
            .first()
        )