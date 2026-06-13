from uuid import uuid4

from app.db.session import SessionLocal
from app.models.alert import AlertSeverity, AlertStatus
from app.models.device import Device, DeviceStatus
from app.services.alert_service import AlertService


def create_test_device():
    db = SessionLocal()

    unique_id = uuid4().hex

    device = Device(
        name=f"Packet Loss Test Device {unique_id}",
        ip_address=f"10.30.{int(unique_id[:2], 16)}.{int(unique_id[2:4], 16)}",
        hostname=f"packet-loss-{unique_id}",
        device_type="router",
        location="test-lab",
        status=DeviceStatus.ONLINE,
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    device_id = device.id
    device_name = device.name

    db.close()

    return device_id, device_name


def test_warning_packet_loss_alert_is_created():
    device_id, device_name = create_test_device()

    db = SessionLocal()

    alert = AlertService.create_packet_loss_alert_if_needed(
        db=db,
        device_id=device_id,
        device_name=device_name,
        packet_loss_percent=10.0,
    )

    assert alert is not None
    assert alert.severity == AlertSeverity.WARNING
    assert alert.status == AlertStatus.OPEN
    assert "Packet loss detected" in alert.message

    db.close()


def test_critical_packet_loss_alert_is_created():
    device_id, device_name = create_test_device()

    db = SessionLocal()

    alert = AlertService.create_packet_loss_alert_if_needed(
        db=db,
        device_id=device_id,
        device_name=device_name,
        packet_loss_percent=25.0,
    )

    assert alert is not None
    assert alert.severity == AlertSeverity.CRITICAL
    assert alert.status == AlertStatus.OPEN
    assert "Packet loss detected" in alert.message

    db.close()


def test_no_packet_loss_alert_below_threshold():
    device_id, device_name = create_test_device()

    db = SessionLocal()

    alert = AlertService.create_packet_loss_alert_if_needed(
        db=db,
        device_id=device_id,
        device_name=device_name,
        packet_loss_percent=2.0,
    )

    assert alert is None

    db.close()