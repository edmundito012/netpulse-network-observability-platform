"""Packet loss burst application orchestration."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.analytics import (
    MetricName,
    MissingValuePolicy,
    SortDirection,
)
from app.repositories.device_metric_repository import (
    DeviceMetricRepository,
)
from app.services.metric_series_service import (
    MetricSeriesResult,
    MetricSeriesService,
)
from app.services.packet_loss_burst_service import (
    PacketLossBurstAnalysisResult,
    PacketLossBurstService,
)


@dataclass(frozen=True, slots=True)
class PacketLossBurstApplicationResult:
    """Burst analysis with its resolved device and source series."""

    device_id: int | None
    series: MetricSeriesResult | None
    analysis: PacketLossBurstAnalysisResult


class PacketLossBurstApplicationService:
    """Retrieve packet loss history and execute burst detection."""

    @classmethod
    def analyze(
        cls,
        db: Session,
        *,
        device_id: int | None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        limit: int = 100,
        warning_threshold_percent: float = 5.0,
        critical_threshold_percent: float = 20.0,
        minimum_consecutive_samples: int = 3,
        maximum_gap_seconds: int = 120,
    ) -> PacketLossBurstApplicationResult:
        """Analyze a real packet loss series for one device."""

        resolved_device_id = cls.resolve_device_id(
            db=db,
            device_id=device_id,
        )

        if resolved_device_id is None:
            analysis = PacketLossBurstService.detect(
                samples=[],
                warning_threshold_percent=(
                    warning_threshold_percent
                ),
                critical_threshold_percent=(
                    critical_threshold_percent
                ),
                minimum_consecutive_samples=(
                    minimum_consecutive_samples
                ),
                maximum_gap_seconds=maximum_gap_seconds,
            )

            return PacketLossBurstApplicationResult(
                device_id=None,
                series=None,
                analysis=analysis,
            )

        series = MetricSeriesService.get_series(
            db=db,
            device_id=resolved_device_id,
            metric_name=MetricName.PACKET_LOSS,
            start_at=start_at,
            end_at=end_at,
            limit=limit,
            sort_direction=SortDirection.ASCENDING,
            missing_value_policy=(
                MissingValuePolicy.PRESERVE
            ),
        )

        analysis = PacketLossBurstService.detect(
            samples=series.samples,
            warning_threshold_percent=(
                warning_threshold_percent
            ),
            critical_threshold_percent=(
                critical_threshold_percent
            ),
            minimum_consecutive_samples=(
                minimum_consecutive_samples
            ),
            maximum_gap_seconds=maximum_gap_seconds,
        )

        return PacketLossBurstApplicationResult(
            device_id=resolved_device_id,
            series=series,
            analysis=analysis,
        )

    @staticmethod
    def resolve_device_id(
        db: Session,
        *,
        device_id: int | None,
    ) -> int | None:
        """Resolve an explicit device or the latest measured device."""

        if device_id is not None:
            return device_id

        return DeviceMetricRepository.get_latest_device_id(
            db,
        )