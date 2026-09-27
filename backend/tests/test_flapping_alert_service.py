from types import SimpleNamespace
from unittest.mock import Mock

from app.models.alert import AlertSeverity, AlertType
from app.models.device import DeviceStatus
from app.services import flapping_alert_service
from app.services.flapping_alert_service import FlappingAlertService


def metric(status):
    return SimpleNamespace(status=status)


def test_returns_none_with_fewer_than_six_metrics(monkeypatch):
    get_latest_status_metrics = Mock(
        return_value=[
            metric(DeviceStatus.ONLINE),
            metric(DeviceStatus.OFFLINE),
            metric(DeviceStatus.ONLINE),
        ]
    )
    create_or_update = Mock()

    monkeypatch.setattr(
        flapping_alert_service.DeviceMetricRepository,
        "get_latest_status_metrics",
        get_latest_status_metrics,
    )
    monkeypatch.setattr(
        flapping_alert_service.AlertDeduplicationService,
        "create_or_update",
        create_or_update,
    )

    result = FlappingAlertService.create_flapping_alert_if_needed(
        db=object(),
        device_id=10,
        device_name="router-01",
    )

    assert result is None
    create_or_update.assert_not_called()


def test_returns_none_with_fewer_than_three_transitions(monkeypatch):
    get_latest_status_metrics = Mock(
        return_value=[
            metric(DeviceStatus.ONLINE),
            metric(DeviceStatus.ONLINE),
            metric(DeviceStatus.OFFLINE),
            metric(DeviceStatus.OFFLINE),
            metric(DeviceStatus.ONLINE),
            metric(DeviceStatus.ONLINE),
        ]
    )
    create_or_update = Mock()

    monkeypatch.setattr(
        flapping_alert_service.DeviceMetricRepository,
        "get_latest_status_metrics",
        get_latest_status_metrics,
    )
    monkeypatch.setattr(
        flapping_alert_service.AlertDeduplicationService,
        "create_or_update",
        create_or_update,
    )

    result = FlappingAlertService.create_flapping_alert_if_needed(
        db=object(),
        device_id=10,
        device_name="router-01",
    )

    assert result is None
    create_or_update.assert_not_called()


def test_creates_warning_at_three_transitions(monkeypatch):
    db = object()
    alert = object()
    get_latest_status_metrics = Mock(
        return_value=[
            metric(DeviceStatus.OFFLINE),
            metric(DeviceStatus.OFFLINE),
            metric(DeviceStatus.OFFLINE),
            metric(DeviceStatus.ONLINE),
            metric(DeviceStatus.OFFLINE),
            metric(DeviceStatus.ONLINE),
        ]
    )
    create_or_update = Mock(return_value=SimpleNamespace(alert=alert))

    monkeypatch.setattr(
        flapping_alert_service.DeviceMetricRepository,
        "get_latest_status_metrics",
        get_latest_status_metrics,
    )
    monkeypatch.setattr(
        flapping_alert_service.AlertDeduplicationService,
        "create_or_update",
        create_or_update,
    )

    result = FlappingAlertService.create_flapping_alert_if_needed(
        db=db,
        device_id=10,
        device_name="router-01",
    )

    assert result is alert
    get_latest_status_metrics.assert_called_once_with(
        db=db,
        device_id=10,
        limit=6,
    )
    create_or_update.assert_called_once_with(
        db=db,
        device_id=10,
        alert_type=AlertType.FLAPPING,
        severity=AlertSeverity.WARNING,
        message="Device flapping detected on router-01",
    )
