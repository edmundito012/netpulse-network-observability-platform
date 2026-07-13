"""Integration tests for alert deduplication persistence."""

from uuid import uuid4

from app.db.session import SessionLocal
from app.models.alert import (
    AlertSeverity,
    AlertStatus,
    AlertType,
)
from app.models.device import (
    Device,
    DeviceStatus,
)
from app.repositories.alert_repository import (
    AlertRepository,
)


def create_device() -> int:
    db = SessionLocal()

    unique_id = uuid4().hex

    device = Device(
        name=f"dedup-device-{unique_id}",
        ip_address=(
            f"10.71."
            f"{int(unique_id[:2], 16)}."
            f"{int(unique_id[2:4], 16)}"
        ),
        hostname=f"dedup-{unique_id}",
        device_type="router",
        location="dedup-test",
        status=DeviceStatus.ONLINE,
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    device_id = device.id

    db.close()

    return device_id


def test_register_occurrence_updates_existing_alert() -> None:
    device_id = create_device()
    db = SessionLocal()

    alert = AlertRepository.create(
        db=db,
        device_id=device_id,
        alert_type=AlertType.PACKET_LOSS,
        deduplication_key=(
            f"device:{device_id}:packet_loss"
        ),
        severity=AlertSeverity.WARNING,
        message="Initial packet loss",
    )

    original_last_seen_at = alert.last_seen_at

    updated_alert = (
        AlertRepository.register_occurrence(
            db=db,
            alert=alert,
            severity=AlertSeverity.CRITICAL,
            message="Critical packet loss",
        )
    )

    assert updated_alert.id == alert.id
    assert updated_alert.occurrence_count == 2
    assert (
        updated_alert.severity
        == AlertSeverity.CRITICAL
    )
    assert (
        updated_alert.message
        == "Critical packet loss"
    )
    assert (
        updated_alert.last_seen_at
        >= original_last_seen_at
    )

    db.close()


def test_resolved_alert_allows_new_alert_with_same_key() -> None:
    device_id = create_device()
    db = SessionLocal()

    deduplication_key = (
        f"device:{device_id}:packet_loss"
    )

    first_alert = AlertRepository.create(
        db=db,
        device_id=device_id,
        alert_type=AlertType.PACKET_LOSS,
        deduplication_key=deduplication_key,
        severity=AlertSeverity.WARNING,
        message="First alert",
    )

    AlertRepository.resolve(
        db=db,
        alert=first_alert,
    )

    second_alert = AlertRepository.create(
        db=db,
        device_id=device_id,
        alert_type=AlertType.PACKET_LOSS,
        deduplication_key=deduplication_key,
        severity=AlertSeverity.WARNING,
        message="Second alert",
    )

    assert first_alert.status == AlertStatus.RESOLVED
    assert second_alert.id != first_alert.id
    assert second_alert.status == AlertStatus.OPEN

    db.close()