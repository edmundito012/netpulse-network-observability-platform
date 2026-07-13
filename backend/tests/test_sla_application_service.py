"""Unit tests for SLA application orchestration."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.models.device import DeviceStatus
from app.services.sla_application_service import (
    SLAApplicationService,
)


@patch(
    "app.services.sla_application_service."
    "SLAService.calculate"
)
@patch(
    "app.services.sla_application_service."
    "DeviceMetricRepository.get_window"
)
def test_calculate_compliance_ignores_missing_measurements(
    get_window_mock: Mock,
    calculate_mock: Mock,
) -> None:
    db = Mock()

    get_window_mock.return_value = [
        SimpleNamespace(
            status=DeviceStatus.ONLINE,
            response_time_ms=0.0,
            packet_loss_percent=0.0,
            jitter_ms=None,
        ),
        SimpleNamespace(
            status=DeviceStatus.OFFLINE,
            response_time_ms=None,
            packet_loss_percent=None,
            jitter_ms=5.0,
        ),
    ]

    expected_result = Mock()
    calculate_mock.return_value = expected_result

    result = SLAApplicationService.calculate_compliance(
        db=db,
        device_id=12,
        start_at=datetime(
            2026,
            7,
            13,
            tzinfo=UTC,
        ),
        end_at=datetime(
            2026,
            7,
            14,
            tzinfo=UTC,
        ),
        limit=100,
    )

    assert result is expected_result

    calculate_mock.assert_called_once_with(
        statuses=["ONLINE", "OFFLINE"],
        latencies_ms=[0.0],
        packet_losses_percent=[0.0],
        jitters_ms=[5.0],
    )


@patch(
    "app.services.sla_application_service."
    "SLAService.calculate"
)
@patch(
    "app.services.sla_application_service."
    "DeviceMetricRepository.get_latest_device_id"
)
def test_calculate_compliance_handles_empty_database(
    get_latest_device_id_mock: Mock,
    calculate_mock: Mock,
) -> None:
    get_latest_device_id_mock.return_value = None

    expected_result = Mock()
    calculate_mock.return_value = expected_result

    result = SLAApplicationService.calculate_compliance(
        db=Mock(),
        device_id=None,
    )

    assert result is expected_result

    calculate_mock.assert_called_once_with(
        statuses=[],
        latencies_ms=[],
        packet_losses_percent=[],
        jitters_ms=[],
    )


@patch(
    "app.services.sla_application_service."
    "DeviceMetricRepository.get_latest_device_id"
)
def test_resolve_device_id_uses_latest_metric_device(
    get_latest_device_id_mock: Mock,
) -> None:
    db = Mock()

    get_latest_device_id_mock.return_value = 19

    result = SLAApplicationService.resolve_device_id(
        db=db,
        device_id=None,
    )

    assert result == 19

    get_latest_device_id_mock.assert_called_once_with(
        db,
    )


def test_normalize_status_handles_enum_values() -> None:
    assert (
        SLAApplicationService.normalize_status(
            DeviceStatus.ONLINE
        )
        == "ONLINE"
    )

    assert (
        SLAApplicationService.normalize_status(
            DeviceStatus.OFFLINE
        )
        == "OFFLINE"
    )


def test_normalize_status_handles_none() -> None:
    assert (
        SLAApplicationService.normalize_status(None)
        == "UNKNOWN"
    )