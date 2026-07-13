"""Temporal metric series application service."""

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.analytics import (
    MetricName,
    MissingValuePolicy,
    SortDirection,
)
from app.models.device_metric import DeviceMetric
from app.repositories.device_metric_repository import (
    DeviceMetricRepository,
)


@dataclass(frozen=True, slots=True)
class MetricSeriesSampleResult:
    """Internal representation of a historical metric sample."""

    metric_id: int
    device_id: int
    checked_at: datetime
    value: float | None


@dataclass(frozen=True, slots=True)
class MetricSeriesResult:
    """Internal representation of a historical metric series."""

    device_id: int
    metric_name: MetricName

    start_at: datetime | None
    end_at: datetime | None

    requested_limit: int
    sort_direction: SortDirection
    missing_value_policy: MissingValuePolicy

    database_sample_count: int
    returned_sample_count: int
    missing_sample_count: int

    samples: list[MetricSeriesSampleResult]


class MetricSeriesService:
    """Retrieve and normalize temporal metric windows."""

    DEFAULT_LIMIT = 100
    MAX_LIMIT = 10_000

    @classmethod
    def get_series(
        cls,
        db: Session,
        *,
        device_id: int,
        metric_name: MetricName,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        limit: int = DEFAULT_LIMIT,
        sort_direction: SortDirection = SortDirection.ASCENDING,
        missing_value_policy: MissingValuePolicy = MissingValuePolicy.DROP,
    ) -> MetricSeriesResult:
        """Return a timestamped metric series for a device.

        Repository ordering is always deterministic. Missing values are
        handled according to an explicit policy and are never silently
        converted to zero.
        """

        cls._validate_window(
            start_at=start_at,
            end_at=end_at,
            limit=limit,
        )

        normalized_start_at = cls._normalize_datetime(start_at)
        normalized_end_at = cls._normalize_datetime(end_at)

        metrics = DeviceMetricRepository.get_window(
            db=db,
            device_id=device_id,
            start_at=normalized_start_at,
            end_at=normalized_end_at,
            limit=limit,
            sort_direction=sort_direction,
        )

        samples: list[MetricSeriesSampleResult] = []
        missing_sample_count = 0

        for metric in metrics:
            value = cls.extract_metric_value(
                metric=metric,
                metric_name=metric_name,
            )

            if value is None:
                missing_sample_count += 1

                if missing_value_policy == MissingValuePolicy.DROP:
                    continue

            samples.append(
                MetricSeriesSampleResult(
                    metric_id=metric.id,
                    device_id=metric.device_id,
                    checked_at=metric.checked_at,
                    value=value,
                )
            )

        return MetricSeriesResult(
            device_id=device_id,
            metric_name=metric_name,
            start_at=normalized_start_at,
            end_at=normalized_end_at,
            requested_limit=limit,
            sort_direction=sort_direction,
            missing_value_policy=missing_value_policy,
            database_sample_count=len(metrics),
            returned_sample_count=len(samples),
            missing_sample_count=missing_sample_count,
            samples=samples,
        )

    @staticmethod
    def extract_metric_value(
        *,
        metric: DeviceMetric,
        metric_name: MetricName,
    ) -> float | None:
        """Extract one supported metric without replacing nulls by zero."""

        if metric_name == MetricName.JITTER:
            return MetricSeriesService._to_float(
                metric.jitter_ms,
            )

        if metric_name == MetricName.PACKET_LOSS:
            return MetricSeriesService._to_float(
                metric.packet_loss_percent,
            )

        return MetricSeriesService._to_float(
            metric.response_time_ms,
        )

    @staticmethod
    def values_from_result(
        result: MetricSeriesResult,
    ) -> list[float]:
        """Return non-null numerical values from a metric result."""

        return [
            sample.value
            for sample in result.samples
            if sample.value is not None
        ]

    @staticmethod
    def _to_float(
        value: float | None,
    ) -> float | None:
        if value is None:
            return None

        return float(value)

    @staticmethod
    def _normalize_datetime(
        value: datetime | None,
    ) -> datetime | None:
        if value is None:
            return None

        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)

        return value.astimezone(UTC)

    @classmethod
    def _validate_window(
        cls,
        *,
        start_at: datetime | None,
        end_at: datetime | None,
        limit: int,
    ) -> None:
        if limit < 1:
            raise ValueError("limit must be greater than or equal to 1")

        if limit > cls.MAX_LIMIT:
            raise ValueError(
                f"limit must be lower than or equal to "
                f"{cls.MAX_LIMIT}"
            )

        if (
            start_at is not None
            and end_at is not None
            and cls._normalize_datetime(start_at)
            > cls._normalize_datetime(end_at)
        ):
            raise ValueError(
                "start_at must be earlier than or equal to end_at"
            )