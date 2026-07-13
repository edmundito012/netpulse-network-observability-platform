"""Compatibility tests for direct Alert ORM construction."""

from uuid import uuid4

from app.db.session import SessionLocal
from app.models.alert import (
    Alert,
    AlertSeverity,
    AlertStatus,
    AlertType,
)
from app.models.device import (
    Device,
    DeviceStatus,
)


def create_test_device() -> int:
    """Persist a device used by direct alert construction tests."""

    db = SessionLocal()

    unique_id = uuid4().hex

    device = Device(
        name=f"legacy-alert-device-{unique_id}",
        ip_address=(
            f"10.72."
            f"{int(unique_id[:2], 16)}."
            f"{int(unique_id[2:4], 16)}"
        ),
        hostname=f"legacy-alert-{unique_id}",
        device_type="router",
        location="alert-model-test",
        status=DeviceStatus.ONLINE,
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    device_id = device.id

    db.close()

    return device_id


def test_direct_alert_construction_generates_legacy_key() -> None:
    """Direct ORM construction remains backwards compatible."""

    device_id = create_test_device()
    db = SessionLocal()

    alert = Alert(
        device_id=device_id,
        severity=AlertSeverity.CRITICAL,
        status=AlertStatus.OPEN,
        message="Directly constructed alert",
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    assert alert.id is not None
    assert alert.alert_type == AlertType.GENERIC
    assert alert.deduplication_key.startswith(
        "legacy:"
    )
    assert alert.occurrence_count == 1
    assert alert.first_seen_at is not None
    assert alert.last_seen_at is not None

    db.close()


def test_direct_generic_alerts_receive_different_keys() -> None:
    """Independent generic alerts must never collide."""

    device_id = create_test_device()
    db = SessionLocal()

    first_alert = Alert(
        device_id=device_id,
        severity=AlertSeverity.WARNING,
        status=AlertStatus.OPEN,
        message="First generic alert",
    )

    second_alert = Alert(
        device_id=device_id,
        severity=AlertSeverity.WARNING,
        status=AlertStatus.OPEN,
        message="Second generic alert",
    )

    db.add_all(
        [
            first_alert,
            second_alert,
        ]
    )

    db.commit()
    db.refresh(first_alert)
    db.refresh(second_alert)

    assert (
        first_alert.deduplication_key
        != second_alert.deduplication_key
    )

    db.close()