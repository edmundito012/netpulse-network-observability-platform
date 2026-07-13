"""Application orchestration for network anomaly analytics."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.analytics import MetricName
from app.repositories.device_metric_repository import (
    DeviceMetricRepository,
)
from app.services.metric_series_service import (
    MetricSeriesResult,
    MetricSeriesService,
)
from app.services.network_anomaly_service import (
    NetworkAnomalyResult,
    NetworkAnomalyService,
)


@dataclass(frozen=True, slots=True)
class NetworkAnomalyAnalysisResult:
    """Combined anomaly result and optional source series."""

    analysis: NetworkAnomalyResult
    series: MetricSeriesResult | None
    resolved_device_id: int | None


class NetworkAnomalyApplicationService:
    """Coordinate metric retrieval and anomaly calculation."""

    @classmethod
    def analyze_device_metric(
        cls,
        db: Session,
        *,
        device_id: int | None,
        metric_name: MetricName,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        limit: int = 20,
    ) -> NetworkAnomalyAnalysisResult:
        """Analyze one coherent device metric series.

        When no device is supplied, the device owning the newest metric
        sample is selected. Measurements from different devices are
        never combined into the same statistical baseline.
        """

        resolved_device_id = cls.resolve_device_id(
            db=db,
            device_id=device_id,
        )

        if resolved_device_id is None:
            analysis = NetworkAnomalyService.analyze(
                values=[],
                metric_name=metric_name.value,
            )

            return NetworkAnomalyAnalysisResult(
                analysis=analysis,
                series=None,
                resolved_device_id=None,
            )

        series = MetricSeriesService.get_series(
            db=db,
            device_id=resolved_device_id,
            metric_name=metric_name,
            start_at=start_at,
            end_at=end_at,
            limit=limit,
        )

        values = MetricSeriesService.values_from_result(
            series,
        )

        analysis = NetworkAnomalyService.analyze(
            values=values,
            metric_name=metric_name.value,
        )

        return NetworkAnomalyAnalysisResult(
            analysis=analysis,
            series=series,
            resolved_device_id=resolved_device_id,
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