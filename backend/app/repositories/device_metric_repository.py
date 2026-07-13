"""Persistence operations for device metric history."""

from datetime import datetime

from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from app.core.analytics import SortDirection
from app.models.device import DeviceStatus
from app.models.device_metric import DeviceMetric


class DeviceMetricRepository:
    """Repository for DeviceMetric persistence and historical queries."""

    @staticmethod
    def create(
        db: Session,
        device_id: int,
        status: DeviceStatus,
        response_time_ms: float | None,
        packet_loss_percent: float | None,
        jitter_ms: float | None,
    ) -> DeviceMetric:
        """Persist a device metric sample."""

        metric = DeviceMetric(
            device_id=device_id,
            status=status,
            response_time_ms=response_time_ms,
            packet_loss_percent=packet_loss_percent,
            jitter_ms=jitter_ms,
        )

        db.add(metric)
        db.commit()
        db.refresh(metric)

        return metric

    @staticmethod
    def get_latest_device_id(
        db: Session,
    ) -> int | None:
        """Return the device ID owning the newest metric sample.

        This method supports backwards-compatible aggregate endpoints
        without combining measurements from unrelated devices.
        """

        statement = (
            select(DeviceMetric.device_id)
            .order_by(
                desc(DeviceMetric.checked_at),
                desc(DeviceMetric.id),
            )
            .limit(1)
        )

        return db.scalar(statement)

    @classmethod
    def get_window(
        cls,
        db: Session,
        *,
        device_id: int,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        limit: int = 100,
        sort_direction: SortDirection = SortDirection.ASCENDING,
    ) -> list[DeviceMetric]:
        """Return metrics inside a deterministic temporal window.

        The database query selects the most recent matching samples.
        Results are subsequently ordered according to the requested
        analytical direction.
        """

        if limit < 1:
            raise ValueError(
                "limit must be greater than or equal to 1"
            )

        statement = cls._build_window_statement(
            device_id=device_id,
            start_at=start_at,
            end_at=end_at,
        )

        recent_metrics = list(
            db.scalars(
                statement
                .order_by(
                    desc(DeviceMetric.checked_at),
                    desc(DeviceMetric.id),
                )
                .limit(limit)
            ).all()
        )

        return sorted(
            recent_metrics,
            key=lambda metric: (
                metric.checked_at,
                metric.id,
            ),
            reverse=(
                sort_direction
                == SortDirection.DESCENDING
            ),
        )

    @staticmethod
    def _build_window_statement(
        *,
        device_id: int,
        start_at: datetime | None,
        end_at: datetime | None,
    ) -> Select[tuple[DeviceMetric]]:
        statement = select(DeviceMetric).where(
            DeviceMetric.device_id == device_id
        )

        if start_at is not None:
            statement = statement.where(
                DeviceMetric.checked_at >= start_at
            )

        if end_at is not None:
            statement = statement.where(
                DeviceMetric.checked_at <= end_at
            )

        return statement

    @staticmethod
    def get_by_device_id(
        db: Session,
        device_id: int,
        limit: int = 50,
    ) -> list[DeviceMetric]:
        """Return recent metrics using the legacy descending contract."""

        statement = (
            select(DeviceMetric)
            .where(
                DeviceMetric.device_id == device_id
            )
            .order_by(
                desc(DeviceMetric.checked_at),
                desc(DeviceMetric.id),
            )
            .limit(limit)
        )

        return list(
            db.scalars(statement).all()
        )

    @staticmethod
    def get_paginated_by_device_id(
        db: Session,
        device_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, object]:
        """Return paginated metrics for a device."""

        query = db.query(DeviceMetric).filter(
            DeviceMetric.device_id == device_id
        )

        total_count = query.count()

        items = (
            query
            .order_by(
                DeviceMetric.checked_at.desc(),
                DeviceMetric.id.desc(),
            )
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
    ) -> DeviceMetric | None:
        """Return the newest metric for a device."""

        statement = (
            select(DeviceMetric)
            .where(
                DeviceMetric.device_id == device_id
            )
            .order_by(
                desc(DeviceMetric.checked_at),
                desc(DeviceMetric.id),
            )
            .limit(1)
        )

        return db.scalar(statement)

    @staticmethod
    def get_latest_metrics(
        db: Session,
        device_id: int,
        limit: int = 5,
    ) -> list[DeviceMetric]:
        """Return recent metrics with a measured response time."""

        statement = (
            select(DeviceMetric)
            .where(
                DeviceMetric.device_id == device_id,
                DeviceMetric.response_time_ms.is_not(None),
            )
            .order_by(
                desc(DeviceMetric.checked_at),
                desc(DeviceMetric.id),
            )
            .limit(limit)
        )

        return list(
            db.scalars(statement).all()
        )

    @staticmethod
    def get_latest_status_metrics(
        db: Session,
        device_id: int,
        limit: int = 6,
    ) -> list[DeviceMetric]:
        """Return recent status samples for a device."""

        statement = (
            select(DeviceMetric)
            .where(
                DeviceMetric.device_id == device_id
            )
            .order_by(
                desc(DeviceMetric.checked_at),
                desc(DeviceMetric.id),
            )
            .limit(limit)
        )

        return list(
            db.scalars(statement).all()
        )