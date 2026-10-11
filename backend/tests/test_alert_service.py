from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.models.alert import (
    AlertSeverity,
    AlertType,
)
from app.models.device_event import DeviceEventType
from app.services.alert_service import AlertService


def test_packet_loss_creates_alert_and_event():
    db = Mock()
    alert = SimpleNamespace(message="Packet loss detected")
    result = SimpleNamespace(
        alert=alert,
        created=True,
    )

    with (
        patch(
            "app.services.alert_service.AlertDeduplicationService.create_or_update",
            return_value=result,
        ) as create_or_update,
        patch(
            "app.services.alert_service.DeviceEventRepository.create",
        ) as create_event,
    ):
        returned_alert = AlertService.create_packet_loss_alert_if_needed(
            db=db,
            device_id=7,
            device_name="Mobile",
            packet_loss_percent=60.0,
        )

    assert returned_alert is alert

    create_or_update.assert_called_once_with(
        db=db,
        device_id=7,
        alert_type=AlertType.PACKET_LOSS,
        severity=AlertSeverity.CRITICAL,
        message="Packet loss detected on Mobile: 60.00%",
    )

    create_event.assert_called_once_with(
        db=db,
        device_id=7,
        event_type=DeviceEventType.ALERT_CREATED,
        message="CRITICAL alert created: Packet loss detected",
    )


def test_repeated_packet_loss_does_not_create_duplicate_event():
    db = Mock()
    alert = SimpleNamespace(message="Packet loss detected")
    result = SimpleNamespace(
        alert=alert,
        created=False,
    )

    with (
        patch(
            "app.services.alert_service.AlertDeduplicationService.create_or_update",
            return_value=result,
        ),
        patch(
            "app.services.alert_service.DeviceEventRepository.create",
        ) as create_event,
    ):
        returned_alert = AlertService.create_packet_loss_alert_if_needed(
            db=db,
            device_id=7,
            device_name="Mobile",
            packet_loss_percent=25.0,
        )

    assert returned_alert is alert
    create_event.assert_not_called()


def test_normal_packet_loss_resolves_active_alert():
    db = Mock()
    active_alert = SimpleNamespace(message="Packet loss detected")
    resolved_alert = SimpleNamespace(message="Packet loss detected")

    with (
        patch(
            "app.services.alert_service."
            "AlertRepository.get_active_by_deduplication_key",
            return_value=active_alert,
        ) as get_active,
        patch(
            "app.services.alert_service.AlertRepository.resolve",
            return_value=resolved_alert,
        ) as resolve,
        patch(
            "app.services.alert_service.DeviceEventRepository.create",
        ) as create_event,
    ):
        returned_alert = AlertService.create_packet_loss_alert_if_needed(
            db=db,
            device_id=7,
            device_name="Mobile",
            packet_loss_percent=0.0,
        )

    assert returned_alert is resolved_alert

    get_active.assert_called_once_with(
        db=db,
        device_id=7,
        deduplication_key="device:7:packet_loss",
    )

    resolve.assert_called_once_with(
        db=db,
        alert=active_alert,
    )

    create_event.assert_called_once_with(
        db=db,
        device_id=7,
        event_type=DeviceEventType.ALERT_RESOLVED,
        message="Alert resolved: Packet loss detected",
    )


def test_normal_packet_loss_without_active_alert_does_nothing():
    db = Mock()

    with (
        patch(
            "app.services.alert_service."
            "AlertRepository.get_active_by_deduplication_key",
            return_value=None,
        ),
        patch(
            "app.services.alert_service.AlertRepository.resolve",
        ) as resolve,
        patch(
            "app.services.alert_service.DeviceEventRepository.create",
        ) as create_event,
    ):
        result = AlertService.create_packet_loss_alert_if_needed(
            db=db,
            device_id=7,
            device_name="Mobile",
            packet_loss_percent=0.0,
        )

    assert result is None
    resolve.assert_not_called()
    create_event.assert_not_called()
