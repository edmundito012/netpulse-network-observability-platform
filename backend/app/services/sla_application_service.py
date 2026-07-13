"""Application orchestration for SLA analytics."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.analytics import SortDirection
from app.models.device_metric import DeviceMetric
from app.repositories.device_metric_repository import (
    DeviceMetricRepository,
)
from app.services.sla_service import (
    SLAResult,
    SLAService,
)


class SLAApplicationService:
    """Retrieve historical metrics and calculate SLA compliance."""

    @classmethod
    def calculate_compliance(
        cls,
        db: Session,
        *,
        device_id: int | None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        limit: int = 100,
    ) -> SLAResult:
        """Calculate SLA from one coherent device metric window.

        When no device is supplied, the device owning the latest metric
        sample is selected. This preserves the previous API contract
        without mixing unrelated devices in the same SLA calculation.
        """

        normalized_start_at = cls._normalize_datetime(
            start_at
        )
        normalized_end_at = cls._normalize_datetime(
            end_at
        )

        cls._validate_window(
            start_at=normalized_start_at,
            end_at=normalized_end_at,
            limit=limit,
        )

        resolved_device_id = cls.resolve_device_id(
            db=db,
            device_id=device_id,
        )

        if resolved_device_id is None:
            return SLAService.calculate(
                statuses=[],
                latencies_ms=[],
                packet_losses_percent=[],
                jitters_ms=[],
            )

        metrics = DeviceMetricRepository.get_window(
            db=db,
            device_id=resolved_device_id,
            start_at=normalized_start_at,
            end_at=normalized_end_at,
            limit=limit,
            sort_direction=SortDirection.ASCENDING,
        )

        statuses = [
            cls.normalize_status(metric.status)
            for metric in metrics
        ]

        latencies = cls._measured_values(
            metrics=metrics,
            attribute_name="response_time_ms",
        )

        packet_losses = cls._measured_values(
            metrics=metrics,
            attribute_name="packet_loss_percent",
        )

        jitters = cls._measured_values(
            metrics=metrics,
            attribute_name="jitter_ms",
        )

        return SLAService.calculate(
            statuses=statuses,
            latencies_ms=latencies,
            packet_losses_percent=packet_losses,
            jitters_ms=jitters,
        )

    @staticmethod
    def resolve_device_id(
        db: Session,
        *,
        device_id: int | None,
    ) -> int | None:
        """Resolve an explicit device or select the latest measured one."""

        if device_id is not None:
            return device_id

        return DeviceMetricRepository.get_latest_device_id(
            db,
        )

    @staticmethod
    def normalize_status(
        status: object,
    ) -> str:
        """Normalize SQLAlchemy enum values for the SLA engine."""

        if status is None:
            return "UNKNOWN"

        value = getattr(
            status,
            "value",
            status,
        )

        normalized = str(value).upper()

        if normalized.endswith(".ONLINE"):
            return "ONLINE"

        if normalized.endswith(".OFFLINE"):
            return "OFFLINE"

        if normalized.endswith(".UNKNOWN"):
            return "UNKNOWN"

        return normalized

    @staticmethod
    def _measured_values(
        *,
        metrics: list[DeviceMetric],
        attribute_name: str,
    ) -> list[float]:
        values: list[float] = []

        for metric in metrics:
            value = getattr(
                metric,
                attribute_name,
            )

            if value is not None:
                values.append(float(value))

        return values

    @staticmethod
    def _normalize_datetime(
        value: datetime | None,
    ) -> datetime | None:
        if value is None:
            return None

        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)

        return value.astimezone(UTC)

    @staticmethod
    def _validate_window(
        *,
        start_at: datetime | None,
        end_at: datetime | None,
        limit: int,
    ) -> None:
        if limit < 1 or limit > 10_000:
            raise ValueError(
                "limit must be between 1 and 10000"
            )

        if (
            start_at is not None
            and end_at is not None
            and start_at > end_at
        ):
            raise ValueError(
                "start_at must be earlier than or equal to end_at"
            )