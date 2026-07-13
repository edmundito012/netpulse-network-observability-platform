"""Unit tests for central alert deduplication."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.models.alert import (
    AlertSeverity,
    AlertType,
)
from app.services.alert_deduplication_service import (
    AlertDeduplicationService,
)


@patch(
    "app.services.alert_deduplication_service."
    "AlertRepository.create"
)
@patch(
    "app.services.alert_deduplication_service."
    "AlertRepository.get_active_by_deduplication_key"
)
def test_creates_alert_when_no_duplicate_exists(
    get_active_mock: Mock,
    create_mock: Mock,
) -> None:
    db = Mock()

    get_active_mock.return_value = None

    created_alert = SimpleNamespace(
        id=1,
    )
    create_mock.return_value = created_alert

    result = (
        AlertDeduplicationService
        .create_or_update(
            db=db,
            device_id=10,
            alert_type=AlertType.PACKET_LOSS,
            severity=AlertSeverity.WARNING,
            message="Packet loss warning",
        )
    )

    assert result.alert is created_alert
    assert result.created is True
    assert result.deduplicated is False
    assert result.severity_escalated is False

    create_mock.assert_called_once_with(
        db=db,
        device_id=10,
        alert_type=AlertType.PACKET_LOSS,
        deduplication_key=(
            "device:10:packet_loss"
        ),
        severity=AlertSeverity.WARNING,
        message="Packet loss warning",
    )


@patch(
    "app.services.alert_deduplication_service."
    "AlertRepository.register_occurrence"
)
@patch(
    "app.services.alert_deduplication_service."
    "AlertRepository.is_more_severe"
)
@patch(
    "app.services.alert_deduplication_service."
    "AlertRepository.get_active_by_deduplication_key"
)
def test_updates_duplicate_alert(
    get_active_mock: Mock,
    is_more_severe_mock: Mock,
    register_occurrence_mock: Mock,
) -> None:
    db = Mock()

    active_alert = SimpleNamespace(
        severity=AlertSeverity.WARNING,
    )

    get_active_mock.return_value = active_alert
    is_more_severe_mock.return_value = False
    register_occurrence_mock.return_value = active_alert

    result = (
        AlertDeduplicationService
        .create_or_update(
            db=db,
            device_id=10,
            alert_type=AlertType.PACKET_LOSS,
            severity=AlertSeverity.WARNING,
            message="Repeated packet loss",
        )
    )

    assert result.created is False
    assert result.deduplicated is True
    assert result.severity_escalated is False

    register_occurrence_mock.assert_called_once_with(
        db=db,
        alert=active_alert,
        severity=AlertSeverity.WARNING,
        message="Repeated packet loss",
    )


@patch(
    "app.services.alert_deduplication_service."
    "AlertRepository.register_occurrence"
)
@patch(
    "app.services.alert_deduplication_service."
    "AlertRepository.is_more_severe"
)
@patch(
    "app.services.alert_deduplication_service."
    "AlertRepository.get_active_by_deduplication_key"
)
def test_duplicate_can_escalate_severity(
    get_active_mock: Mock,
    is_more_severe_mock: Mock,
    register_occurrence_mock: Mock,
) -> None:
    db = Mock()

    active_alert = SimpleNamespace(
        severity=AlertSeverity.WARNING,
    )

    get_active_mock.return_value = active_alert
    is_more_severe_mock.return_value = True
    register_occurrence_mock.return_value = active_alert

    result = (
        AlertDeduplicationService
        .create_or_update(
            db=db,
            device_id=10,
            alert_type=AlertType.PACKET_LOSS,
            severity=AlertSeverity.CRITICAL,
            message="Critical packet loss",
        )
    )

    assert result.created is False
    assert result.deduplicated is True
    assert result.severity_escalated is True


def test_different_alert_types_have_different_keys() -> None:
    packet_loss_key = (
        AlertDeduplicationService
        .build_deduplication_key(
            device_id=15,
            alert_type=AlertType.PACKET_LOSS,
        )
    )

    latency_key = (
        AlertDeduplicationService
        .build_deduplication_key(
            device_id=15,
            alert_type=AlertType.LATENCY_TREND,
        )
    )

    assert packet_loss_key != latency_key