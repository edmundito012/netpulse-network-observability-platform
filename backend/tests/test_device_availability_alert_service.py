from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.models.alert import (
    AlertSeverity,
    AlertType,
)
from app.models.device import DeviceStatus
from app.models.device_event import DeviceEventType
from app.services.device_availability_alert_service import (
    DeviceAvailabilityAlertService,
)


def test_offline_creates_availability_alert_and_event():
    db = Mock()
    alert = SimpleNamespace(message="Device Mobile is offline")
    result = SimpleNamespace(
        alert=alert,
        created=True,
    )

    with (
        patch(
            "app.services.device_availability_alert_service."
            "AlertDeduplicationService.create_or_update",
            return_value=result,
        ) as create_or_update,
        patch(
            "app.services.device_availability_alert_service."
            "DeviceEventRepository.create",
        ) as create_event,
    ):
        returned_alert = DeviceAvailabilityAlertService.reconcile(
            db=db,
            device_id=7,
            device_name="Mobile",
            status=DeviceStatus.OFFLINE,
        )

    assert returned_alert is alert

    create_or_update.assert_called_once_with(
        db=db,
        device_id=7,
        alert_type=AlertType.DEVICE_OFFLINE,
        severity=AlertSeverity.CRITICAL,
        message="Device Mobile is offline",
    )

    create_event.assert_called_once_with(
        db=db,
        device_id=7,
        event_type=DeviceEventType.ALERT_CREATED,
        message="Critical alert created: Device Mobile is offline",
    )


def test_repeated_offline_deduplicates_without_new_event():
    db = Mock()
    alert = SimpleNamespace(message="Device Mobile is offline")
    result = SimpleNamespace(
        alert=alert,
        created=False,
    )

    with (
        patch(
            "app.services.device_availability_alert_service."
            "AlertDeduplicationService.create_or_update",
            return_value=result,
        ),
        patch(
            "app.services.device_availability_alert_service."
            "DeviceEventRepository.create",
        ) as create_event,
    ):
        returned_alert = DeviceAvailabilityAlertService.reconcile(
            db=db,
            device_id=7,
            device_name="Mobile",
            status=DeviceStatus.OFFLINE,
        )

    assert returned_alert is alert
    create_event.assert_not_called()


def test_online_resolves_only_device_offline_alert():
    db = Mock()
    active_alert = SimpleNamespace(message="Device Mobile is offline")
    resolved_alert = SimpleNamespace(message="Device Mobile is offline")

    with (
        patch(
            "app.services.device_availability_alert_service."
            "AlertRepository.get_active_by_deduplication_key",
            return_value=active_alert,
        ) as get_active,
        patch(
            "app.services.device_availability_alert_service.AlertRepository.resolve",
            return_value=resolved_alert,
        ) as resolve,
        patch(
            "app.services.device_availability_alert_service."
            "DeviceEventRepository.create",
        ) as create_event,
    ):
        returned_alert = DeviceAvailabilityAlertService.reconcile(
            db=db,
            device_id=7,
            device_name="Mobile",
            status=DeviceStatus.ONLINE,
        )

    assert returned_alert is resolved_alert

    get_active.assert_called_once_with(
        db=db,
        device_id=7,
        deduplication_key="device:7:device_offline",
    )

    resolve.assert_called_once_with(
        db=db,
        alert=active_alert,
    )

    create_event.assert_called_once_with(
        db=db,
        device_id=7,
        event_type=DeviceEventType.ALERT_RESOLVED,
        message="Alert resolved: Device Mobile is offline",
    )


def test_online_without_offline_alert_does_nothing():
    db = Mock()

    with (
        patch(
            "app.services.device_availability_alert_service."
            "AlertRepository.get_active_by_deduplication_key",
            return_value=None,
        ),
        patch(
            "app.services.device_availability_alert_service.AlertRepository.resolve",
        ) as resolve,
        patch(
            "app.services.device_availability_alert_service."
            "DeviceEventRepository.create",
        ) as create_event,
    ):
        result = DeviceAvailabilityAlertService.reconcile(
            db=db,
            device_id=7,
            device_name="Mobile",
            status=DeviceStatus.ONLINE,
        )

    assert result is None
    resolve.assert_not_called()
    create_event.assert_not_called()


def test_unknown_status_does_not_change_alerts():
    db = Mock()

    with (
        patch(
            "app.services.device_availability_alert_service."
            "AlertDeduplicationService.create_or_update",
        ) as create_or_update,
        patch(
            "app.services.device_availability_alert_service."
            "AlertRepository.get_active_by_deduplication_key",
        ) as get_active,
    ):
        result = DeviceAvailabilityAlertService.reconcile(
            db=db,
            device_id=7,
            device_name="Mobile",
            status=DeviceStatus.UNKNOWN,
        )

    assert result is None
    create_or_update.assert_not_called()
    get_active.assert_not_called()
