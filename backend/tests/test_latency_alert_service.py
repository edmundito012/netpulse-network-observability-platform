from types import SimpleNamespace
from unittest.mock import Mock

from app.models.alert import AlertSeverity, AlertType
from app.services import latency_alert_service
from app.services.latency_alert_service import LatencyAlertService


def metric(response_time_ms):
    return SimpleNamespace(response_time_ms=response_time_ms)


def test_returns_none_with_fewer_than_five_metrics(monkeypatch):
    get_latest_metrics = Mock(
        return_value=[
            metric(30.0),
            metric(20.0),
            metric(10.0),
        ]
    )
    create_or_update = Mock()

    monkeypatch.setattr(
        latency_alert_service.DeviceMetricRepository,
        "get_latest_metrics",
        get_latest_metrics,
    )
    monkeypatch.setattr(
        latency_alert_service.AlertDeduplicationService,
        "create_or_update",
        create_or_update,
    )

    result = LatencyAlertService.create_latency_trend_alert_if_needed(
        db=object(),
        device_id=10,
        device_name="router-01",
    )

    assert result is None
    create_or_update.assert_not_called()


def test_returns_none_when_metric_has_no_latency(monkeypatch):
    get_latest_metrics = Mock(
        return_value=[
            metric(50.0),
            metric(40.0),
            metric(None),
            metric(20.0),
            metric(10.0),
        ]
    )
    create_or_update = Mock()

    monkeypatch.setattr(
        latency_alert_service.DeviceMetricRepository,
        "get_latest_metrics",
        get_latest_metrics,
    )
    monkeypatch.setattr(
        latency_alert_service.AlertDeduplicationService,
        "create_or_update",
        create_or_update,
    )

    result = LatencyAlertService.create_latency_trend_alert_if_needed(
        db=object(),
        device_id=10,
        device_name="router-01",
    )

    assert result is None
    create_or_update.assert_not_called()


def test_returns_none_when_latency_is_not_strictly_increasing(monkeypatch):
    get_latest_metrics = Mock(
        return_value=[
            metric(50.0),
            metric(40.0),
            metric(40.0),
            metric(20.0),
            metric(10.0),
        ]
    )
    create_or_update = Mock()

    monkeypatch.setattr(
        latency_alert_service.DeviceMetricRepository,
        "get_latest_metrics",
        get_latest_metrics,
    )
    monkeypatch.setattr(
        latency_alert_service.AlertDeduplicationService,
        "create_or_update",
        create_or_update,
    )

    result = LatencyAlertService.create_latency_trend_alert_if_needed(
        db=object(),
        device_id=10,
        device_name="router-01",
    )

    assert result is None
    create_or_update.assert_not_called()


def test_creates_warning_for_strictly_increasing_latency(monkeypatch):
    db = object()
    alert = object()
    get_latest_metrics = Mock(
        return_value=[
            metric(50.0),
            metric(40.0),
            metric(30.0),
            metric(20.0),
            metric(10.0),
        ]
    )
    create_or_update = Mock(return_value=SimpleNamespace(alert=alert))

    monkeypatch.setattr(
        latency_alert_service.DeviceMetricRepository,
        "get_latest_metrics",
        get_latest_metrics,
    )
    monkeypatch.setattr(
        latency_alert_service.AlertDeduplicationService,
        "create_or_update",
        create_or_update,
    )

    result = LatencyAlertService.create_latency_trend_alert_if_needed(
        db=db,
        device_id=10,
        device_name="router-01",
    )

    assert result is alert
    get_latest_metrics.assert_called_once_with(
        db=db,
        device_id=10,
        limit=5,
    )
    create_or_update.assert_called_once_with(
        db=db,
        device_id=10,
        alert_type=AlertType.LATENCY_TREND,
        severity=AlertSeverity.WARNING,
        message="Latency degradation detected on router-01",
    )
