from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.main import app
from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.models.device import Device, DeviceStatus
from app.models.user import User, UserRole


client = TestClient(app)


def create_test_admin():
    db = SessionLocal()

    email = f"alerts_admin_{uuid4().hex}@test.com"
    username = f"alerts_admin_{uuid4().hex}"

    user = User(
        email=email,
        username=username,
        hashed_password=hash_password("admin123"),
        role=UserRole.ADMIN,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    return email


def get_admin_token():
    email = create_test_admin()

    response = client.post(
        "/auth/login",
        data={
            "username": email,
            "password": "admin123",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def create_test_device_and_alert():
    db = SessionLocal()

    unique_id = uuid4().hex

    device = Device(
        name=f"Alert Test Device {unique_id}",
        ip_address=f"10.10.{int(unique_id[:2], 16)}.{int(unique_id[2:4], 16)}",
        hostname=f"alert-device-{unique_id}",
        device_type="router",
        location="test-lab",
        status=DeviceStatus.OFFLINE,
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    alert = Alert(
        device_id=device.id,
        severity=AlertSeverity.CRITICAL,
        status=AlertStatus.OPEN,
        message="Test critical alert",
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    alert_id = alert.id

    db.close()

    return alert_id


def test_list_alerts():
    token = get_admin_token()

    response = client.get(
        "/alerts/",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert "items" in response.json()


def test_get_open_alerts():
    token = get_admin_token()

    response = client.get(
        "/alerts/open",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_alert_by_id():
    token = get_admin_token()
    alert_id = create_test_device_and_alert()

    response = client.get(
        f"/alerts/{alert_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == alert_id


def test_acknowledge_alert():
    token = get_admin_token()
    alert_id = create_test_device_and_alert()

    response = client.post(
        f"/alerts/{alert_id}/acknowledge",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ACKNOWLEDGED"


def test_resolve_alert():
    token = get_admin_token()
    alert_id = create_test_device_and_alert()

    response = client.post(
        f"/alerts/{alert_id}/resolve",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "RESOLVED"


def test_alerts_requires_auth():
    response = client.get("/alerts/")

    assert response.status_code in [401, 403]