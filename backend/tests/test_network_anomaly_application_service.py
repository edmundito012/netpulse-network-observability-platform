"""Unit tests for anomaly application orchestration."""

from unittest.mock import Mock, patch

from app.core.analytics import MetricName
from app.services.metric_series_service import (
    MetricSeriesResult,
)
from app.services.network_anomaly_application_service import (
    NetworkAnomalyApplicationService,
)


@patch(
    "app.services.network_anomaly_application_service."
    "NetworkAnomalyService.analyze"
)
@patch(
    "app.services.network_anomaly_application_service."
    "MetricSeriesService.get_series"
)
def test_anomaly_application_uses_only_measured_values(
    get_series_mock: Mock,
    analyze_mock: Mock,
) -> None:
    series = Mock(spec=MetricSeriesResult)

    get_series_mock.return_value = series

    with patch(
        "app.services.network_anomaly_application_service."
        "MetricSeriesService.values_from_result",
        return_value=[10.0, 20.0, 30.0],
    ) as values_mock:
        expected_analysis = Mock()
        analyze_mock.return_value = expected_analysis

        result = (
            NetworkAnomalyApplicationService
            .analyze_device_metric(
                db=Mock(),
                device_id=15,
                metric_name=MetricName.LATENCY,
                limit=20,
            )
        )

    values_mock.assert_called_once_with(series)

    analyze_mock.assert_called_once_with(
        values=[10.0, 20.0, 30.0],
        metric_name="latency",
    )

    assert result.series is series
    assert result.analysis is expected_analysis
    assert result.resolved_device_id == 15


@patch(
    "app.services.network_anomaly_application_service."
    "NetworkAnomalyService.analyze"
)
@patch(
    "app.services.network_anomaly_application_service."
    "DeviceMetricRepository.get_latest_device_id"
)
def test_anomaly_application_returns_empty_analysis_without_metrics(
    get_latest_device_id_mock: Mock,
    analyze_mock: Mock,
) -> None:
    get_latest_device_id_mock.return_value = None

    expected_analysis = Mock()
    analyze_mock.return_value = expected_analysis

    result = (
        NetworkAnomalyApplicationService
        .analyze_device_metric(
            db=Mock(),
            device_id=None,
            metric_name=MetricName.LATENCY,
        )
    )

    analyze_mock.assert_called_once_with(
        values=[],
        metric_name="latency",
    )

    assert result.analysis is expected_analysis
    assert result.series is None
    assert result.resolved_device_id is None


@patch(
    "app.services.network_anomaly_application_service."
    "DeviceMetricRepository.get_latest_device_id"
)
def test_resolve_device_id_uses_latest_metric_device(
    get_latest_device_id_mock: Mock,
) -> None:
    db = Mock()

    get_latest_device_id_mock.return_value = 25

    result = (
        NetworkAnomalyApplicationService
        .resolve_device_id(
            db=db,
            device_id=None,
        )
    )

    assert result == 25

    get_latest_device_id_mock.assert_called_once_with(
        db,
    )