"""Unit tests for temporal metric series normalization."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from app.core.analytics import (
    MetricName,
    MissingValuePolicy,
    SortDirection,
)
from app.services.metric_series_service import (
    MetricSeriesService,
)


def build_metric(
    *,
    metric_id: int,
    checked_at: datetime,
    response_time_ms: float | None = None,
    jitter_ms: float | None = None,
    packet_loss_percent: float | None = None,
):
    return SimpleNamespace(
        id=metric_id,
        device_id=10,
        checked_at=checked_at,
        response_time_ms=response_time_ms,
        jitter_ms=jitter_ms,
        packet_loss_percent=packet_loss_percent,
    )


@patch(
    "app.services.metric_series_service."
    "DeviceMetricRepository.get_window"
)
def test_get_series_drops_missing_values_without_using_zero(
    get_window_mock: Mock,
) -> None:
    get_window_mock.return_value = [
        build_metric(
            metric_id=1,
            checked_at=datetime(
                2026,
                7,
                13,
                10,
                0,
                tzinfo=UTC,
            ),
            packet_loss_percent=None,
        ),
        build_metric(
            metric_id=2,
            checked_at=datetime(
                2026,
                7,
                13,
                10,
                1,
                tzinfo=UTC,
            ),
            packet_loss_percent=0.0,
        ),
    ]

    result = MetricSeriesService.get_series(
        db=Mock(),
        device_id=10,
        metric_name=MetricName.PACKET_LOSS,
        limit=100,
        missing_value_policy=MissingValuePolicy.DROP,
    )

    assert result.database_sample_count == 2
    assert result.returned_sample_count == 1
    assert result.missing_sample_count == 1
    assert len(result.samples) == 1
    assert result.samples[0].value == 0.0


@patch(
    "app.services.metric_series_service."
    "DeviceMetricRepository.get_window"
)
def test_get_series_preserves_missing_values_when_requested(
    get_window_mock: Mock,
) -> None:
    get_window_mock.return_value = [
        build_metric(
            metric_id=1,
            checked_at=datetime(
                2026,
                7,
                13,
                10,
                0,
                tzinfo=UTC,
            ),
            jitter_ms=None,
        )
    ]

    result = MetricSeriesService.get_series(
        db=Mock(),
        device_id=10,
        metric_name=MetricName.JITTER,
        missing_value_policy=MissingValuePolicy.PRESERVE,
    )

    assert result.database_sample_count == 1
    assert result.returned_sample_count == 1
    assert result.missing_sample_count == 1
    assert result.samples[0].value is None


@patch(
    "app.services.metric_series_service."
    "DeviceMetricRepository.get_window"
)
def test_values_from_result_only_returns_measured_values(
    get_window_mock: Mock,
) -> None:
    get_window_mock.return_value = [
        build_metric(
            metric_id=1,
            checked_at=datetime.now(UTC),
            response_time_ms=0.0,
        ),
        build_metric(
            metric_id=2,
            checked_at=datetime.now(UTC),
            response_time_ms=None,
        ),
        build_metric(
            metric_id=3,
            checked_at=datetime.now(UTC),
            response_time_ms=15.5,
        ),
    ]

    result = MetricSeriesService.get_series(
        db=Mock(),
        device_id=10,
        metric_name=MetricName.LATENCY,
        missing_value_policy=MissingValuePolicy.PRESERVE,
    )

    assert MetricSeriesService.values_from_result(
        result
    ) == [0.0, 15.5]


def test_get_series_rejects_invalid_temporal_window() -> None:
    with pytest.raises(
        ValueError,
        match="start_at must be earlier",
    ):
        MetricSeriesService.get_series(
            db=Mock(),
            device_id=10,
            metric_name=MetricName.LATENCY,
            start_at=datetime(
                2026,
                7,
                14,
                tzinfo=UTC,
            ),
            end_at=datetime(
                2026,
                7,
                13,
                tzinfo=UTC,
            ),
        )


@pytest.mark.parametrize(
    "limit",
    [0, -1, 10_001],
)
def test_get_series_rejects_invalid_limits(
    limit: int,
) -> None:
    with pytest.raises(ValueError):
        MetricSeriesService.get_series(
            db=Mock(),
            device_id=10,
            metric_name=MetricName.LATENCY,
            limit=limit,
        )


@patch(
    "app.services.metric_series_service."
    "DeviceMetricRepository.get_window"
)
def test_get_series_passes_window_to_repository(
    get_window_mock: Mock,
) -> None:
    get_window_mock.return_value = []

    db = Mock()

    start_at = datetime(
        2026,
        7,
        13,
        9,
        0,
        tzinfo=UTC,
    )
    end_at = datetime(
        2026,
        7,
        13,
        10,
        0,
        tzinfo=UTC,
    )

    MetricSeriesService.get_series(
        db=db,
        device_id=42,
        metric_name=MetricName.LATENCY,
        start_at=start_at,
        end_at=end_at,
        limit=50,
        sort_direction=SortDirection.ASCENDING,
    )

    get_window_mock.assert_called_once_with(
        db=db,
        device_id=42,
        start_at=start_at,
        end_at=end_at,
        limit=50,
        sort_direction=SortDirection.ASCENDING,
    )