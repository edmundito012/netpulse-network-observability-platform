import asyncio
from unittest.mock import AsyncMock, Mock, call

import pytest

from app.models.device import DeviceStatus
from app.services import monitoring_service
from app.services.monitoring_service import MonitoringService


def test_ping_device_calculates_average_and_jitter(monkeypatch):
    ping = Mock(
        side_effect=[
            0.010,
            0.020,
            0.040,
        ]
    )
    monkeypatch.setattr(monitoring_service, "ping", ping)

    status, latency_ms, packet_loss, jitter_ms = MonitoringService.ping_device(
        ip_address="192.0.2.10",
        attempts=3,
    )

    assert status is DeviceStatus.ONLINE
    assert latency_ms == pytest.approx(23.333333)
    assert packet_loss == 0.0
    assert jitter_ms == pytest.approx(15.0)
    assert ping.call_args_list == [
        call(
            "192.0.2.10",
            timeout=monitoring_service.settings.PING_TIMEOUT_SECONDS,
        ),
        call(
            "192.0.2.10",
            timeout=monitoring_service.settings.PING_TIMEOUT_SECONDS,
        ),
        call(
            "192.0.2.10",
            timeout=monitoring_service.settings.PING_TIMEOUT_SECONDS,
        ),
    ]


def test_ping_device_calculates_partial_packet_loss(monkeypatch):
    monkeypatch.setattr(
        monitoring_service,
        "ping",
        Mock(
            side_effect=[
                0.010,
                None,
                0.030,
                None,
            ]
        ),
    )

    status, latency_ms, packet_loss, jitter_ms = MonitoringService.ping_device(
        ip_address="192.0.2.20",
        attempts=4,
    )

    assert status is DeviceStatus.ONLINE
    assert latency_ms == pytest.approx(20.0)
    assert packet_loss == 50.0
    assert jitter_ms == pytest.approx(20.0)


@pytest.mark.parametrize("failed_response", [None, False])
def test_ping_device_returns_offline_when_all_attempts_fail(
    monkeypatch,
    failed_response,
):
    monkeypatch.setattr(
        monitoring_service,
        "ping",
        Mock(return_value=failed_response),
    )

    result = MonitoringService.ping_device(
        ip_address="192.0.2.30",
        attempts=3,
    )

    assert result == (
        DeviceStatus.OFFLINE,
        None,
        100.0,
        0.0,
    )


def test_ping_device_returns_zero_jitter_for_single_success(monkeypatch):
    monkeypatch.setattr(
        monitoring_service,
        "ping",
        Mock(side_effect=[0.025, None]),
    )

    status, latency_ms, packet_loss, jitter_ms = MonitoringService.ping_device(
        ip_address="192.0.2.40",
        attempts=2,
    )

    assert status is DeviceStatus.ONLINE
    assert latency_ms == pytest.approx(25.0)
    assert packet_loss == 50.0
    assert jitter_ms == 0.0


def test_ping_device_converts_ping_error_to_offline(monkeypatch):
    monkeypatch.setattr(
        monitoring_service,
        "ping",
        Mock(side_effect=OSError("permission denied")),
    )

    result = MonitoringService.ping_device(
        ip_address="192.0.2.50",
        attempts=3,
    )

    assert result == (
        DeviceStatus.OFFLINE,
        None,
        100.0,
        0.0,
    )


def test_ping_device_async_delegates_to_thread(monkeypatch):
    expected = (
        DeviceStatus.ONLINE,
        12.0,
        0.0,
        1.0,
    )
    to_thread = AsyncMock(return_value=expected)
    monkeypatch.setattr(
        monitoring_service.asyncio,
        "to_thread",
        to_thread,
    )

    result = asyncio.run(MonitoringService.ping_device_async("192.0.2.60"))

    assert result == expected
    to_thread.assert_awaited_once_with(
        MonitoringService.ping_device,
        "192.0.2.60",
    )
