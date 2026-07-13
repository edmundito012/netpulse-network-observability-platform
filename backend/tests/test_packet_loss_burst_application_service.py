"""Tests for packet loss burst application orchestration."""

from unittest.mock import Mock, patch

from app.core.analytics import (
    MetricName,
    MissingValuePolicy,
    SortDirection,
)
from app.services.metric_series_service import (
    MetricSeriesResult,
)
from app.services.packet_loss_burst_application_service import (
    PacketLossBurstApplicationService,
)


@patch(
    "app.services.packet_loss_burst_application_service."
    "PacketLossBurstService.detect"
)
@patch(
    "app.services.packet_loss_burst_application_service."
    "MetricSeriesService.get_series"
)
def test_application_service_uses_packet_loss_series(
    get_series_mock: Mock,
    detect_mock: Mock,
) -> None:
    db = Mock()
    series = Mock(spec=MetricSeriesResult)

    get_series_mock.return_value = series
    expected_analysis = Mock()
    detect_mock.return_value = expected_analysis

    result = PacketLossBurstApplicationService.analyze(
        db=db,
        device_id=12,
        limit=50,
    )

    get_series_mock.assert_called_once_with(
        db=db,
        device_id=12,
        metric_name=MetricName.PACKET_LOSS,
        start_at=None,
        end_at=None,
        limit=50,
        sort_direction=SortDirection.ASCENDING,
        missing_value_policy=(
            MissingValuePolicy.PRESERVE
        ),
    )

    detect_mock.assert_called_once_with(
        samples=series.samples,
        warning_threshold_percent=5.0,
        critical_threshold_percent=20.0,
        minimum_consecutive_samples=3,
        maximum_gap_seconds=120,
    )

    assert result.device_id == 12
    assert result.series is series
    assert result.analysis is expected_analysis


@patch(
    "app.services.packet_loss_burst_application_service."
    "PacketLossBurstService.detect"
)
@patch(
    "app.services.packet_loss_burst_application_service."
    "DeviceMetricRepository.get_latest_device_id"
)
def test_application_service_handles_empty_database(
    get_latest_device_id_mock: Mock,
    detect_mock: Mock,
) -> None:
    get_latest_device_id_mock.return_value = None

    expected_analysis = Mock()
    detect_mock.return_value = expected_analysis

    result = PacketLossBurstApplicationService.analyze(
        db=Mock(),
        device_id=None,
    )

    detect_mock.assert_called_once_with(
        samples=[],
        warning_threshold_percent=5.0,
        critical_threshold_percent=20.0,
        minimum_consecutive_samples=3,
        maximum_gap_seconds=120,
    )

    assert result.device_id is None
    assert result.series is None
    assert result.analysis is expected_analysis