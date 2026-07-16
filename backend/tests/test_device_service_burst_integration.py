"""Tests for DeviceService packet loss burst integration."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.services.device_service import DeviceService


@patch(
    "app.services.device_service."
    "PacketLossBurstIncidentService.evaluate"
)
@patch(
    "app.services.device_service."
    "FlappingAlertService."
    "create_flapping_alert_if_needed"
)
@patch(
    "app.services.device_service."
    "LatencyAlertService."
    "create_latency_trend_alert_if_needed"
)
@patch(
    "app.services.device_service."
    "AlertService."
    "create_packet_loss_alert_if_needed"
)
@patch(
    "app.services.device_service."
    "JitterAlertService.evaluate"
)
@patch(
    "app.services.device_service."
    "DeviceMetricRepository.create"
)
@patch(
    "app.services.device_service."
    "MonitoringService.ping_device"
)
@patch(
    "app.services.device_service."
    "DeviceRepository.get_by_id"
)
def test_ping_evaluates_burst_after_metric_persistence(
    get_device_mock: Mock,
    ping_mock: Mock,
    create_metric_mock: Mock,
    jitter_mock: Mock,
    packet_loss_alert_mock: Mock,
    latency_alert_mock: Mock,
    flapping_alert_mock: Mock,
    burst_incident_mock: Mock,
) -> None:
    db = Mock()

    device = SimpleNamespace(
        id=10,
        name="Router Madrid",
        ip_address="10.0.0.10",
        status=None,
    )

    get_device_mock.return_value = device

    ping_mock.return_value = (
        "ONLINE",
        20.0,
        25.0,
        3.0,
    )

    jitter_mock.return_value = None

    result = DeviceService.ping_device(
        db=db,
        device_id=10,
    )

    assert result is device

    create_metric_mock.assert_called_once_with(
        db=db,
        device_id=10,
        status="ONLINE",
        response_time_ms=20.0,
        packet_loss_percent=25.0,
        jitter_ms=3.0,
    )

    burst_incident_mock.assert_called_once_with(
        db=db,
        device_id=10,
        device_name="Router Madrid",
    )

    assert (
        create_metric_mock.call_args_list
        and burst_incident_mock.call_args_list
    )