from types import SimpleNamespace
from unittest.mock import Mock

from app.models.device import DeviceStatus
from app.services import device_status_confirmation_service
from app.services.device_status_confirmation_service import (
    DeviceStatusConfirmationService,
)


def metric(status: DeviceStatus):
    return SimpleNamespace(status=status)


def test_keeps_current_status_when_observation_matches(monkeypatch):
    get_latest_status_metrics = Mock()

    monkeypatch.setattr(
        device_status_confirmation_service.DeviceMetricRepository,
        "get_latest_status_metrics",
        get_latest_status_metrics,
    )

    result = DeviceStatusConfirmationService.confirm(
        db=object(),
        device_id=7,
        current_status=DeviceStatus.ONLINE,
        observed_status=DeviceStatus.ONLINE,
    )

    assert result == DeviceStatus.ONLINE
    get_latest_status_metrics.assert_not_called()


def test_confirms_offline_after_required_cycles(monkeypatch):
    db = object()
    get_latest_status_metrics = Mock(
        return_value=[
            metric(DeviceStatus.OFFLINE),
            metric(DeviceStatus.OFFLINE),
            metric(DeviceStatus.OFFLINE),
        ]
    )

    monkeypatch.setattr(
        device_status_confirmation_service.DeviceMetricRepository,
        "get_latest_status_metrics",
        get_latest_status_metrics,
    )

    result = DeviceStatusConfirmationService.confirm(
        db=db,
        device_id=7,
        current_status=DeviceStatus.ONLINE,
        observed_status=DeviceStatus.OFFLINE,
    )

    assert result == DeviceStatus.OFFLINE
    get_latest_status_metrics.assert_called_once_with(
        db=db,
        device_id=7,
        limit=3,
    )


def test_keeps_online_with_insufficient_offline_cycles(monkeypatch):
    monkeypatch.setattr(
        device_status_confirmation_service.DeviceMetricRepository,
        "get_latest_status_metrics",
        Mock(
            return_value=[
                metric(DeviceStatus.OFFLINE),
                metric(DeviceStatus.OFFLINE),
            ]
        ),
    )

    result = DeviceStatusConfirmationService.confirm(
        db=object(),
        device_id=7,
        current_status=DeviceStatus.ONLINE,
        observed_status=DeviceStatus.OFFLINE,
    )

    assert result == DeviceStatus.ONLINE


def test_keeps_online_when_offline_sequence_is_interrupted(monkeypatch):
    monkeypatch.setattr(
        device_status_confirmation_service.DeviceMetricRepository,
        "get_latest_status_metrics",
        Mock(
            return_value=[
                metric(DeviceStatus.OFFLINE),
                metric(DeviceStatus.ONLINE),
                metric(DeviceStatus.OFFLINE),
            ]
        ),
    )

    result = DeviceStatusConfirmationService.confirm(
        db=object(),
        device_id=7,
        current_status=DeviceStatus.ONLINE,
        observed_status=DeviceStatus.OFFLINE,
    )

    assert result == DeviceStatus.ONLINE


def test_confirms_online_after_required_cycles(monkeypatch):
    db = object()
    get_latest_status_metrics = Mock(
        return_value=[
            metric(DeviceStatus.ONLINE),
            metric(DeviceStatus.ONLINE),
        ]
    )

    monkeypatch.setattr(
        device_status_confirmation_service.DeviceMetricRepository,
        "get_latest_status_metrics",
        get_latest_status_metrics,
    )

    result = DeviceStatusConfirmationService.confirm(
        db=db,
        device_id=7,
        current_status=DeviceStatus.OFFLINE,
        observed_status=DeviceStatus.ONLINE,
    )

    assert result == DeviceStatus.ONLINE
    get_latest_status_metrics.assert_called_once_with(
        db=db,
        device_id=7,
        limit=2,
    )


def test_keeps_offline_with_single_online_cycle(monkeypatch):
    monkeypatch.setattr(
        device_status_confirmation_service.DeviceMetricRepository,
        "get_latest_status_metrics",
        Mock(
            return_value=[
                metric(DeviceStatus.ONLINE),
            ]
        ),
    )

    result = DeviceStatusConfirmationService.confirm(
        db=object(),
        device_id=7,
        current_status=DeviceStatus.OFFLINE,
        observed_status=DeviceStatus.ONLINE,
    )

    assert result == DeviceStatus.OFFLINE


def test_ignores_unknown_observation(monkeypatch):
    get_latest_status_metrics = Mock()

    monkeypatch.setattr(
        device_status_confirmation_service.DeviceMetricRepository,
        "get_latest_status_metrics",
        get_latest_status_metrics,
    )

    result = DeviceStatusConfirmationService.confirm(
        db=object(),
        device_id=7,
        current_status=DeviceStatus.ONLINE,
        observed_status=DeviceStatus.UNKNOWN,
    )

    assert result == DeviceStatus.ONLINE
    get_latest_status_metrics.assert_not_called()
