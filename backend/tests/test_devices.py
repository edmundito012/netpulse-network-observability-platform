from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.main import app
from app.models.user import User, UserRole


client = TestClient(app)


def create_test_admin():
    db = SessionLocal()

    email = f"devices_admin_{uuid4().hex}@test.com"
    username = f"devices_admin_{uuid4().hex}"

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


def test_list_devices():
    token = get_admin_token()

    response = client.get(
        "/devices/",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_device():
    token = get_admin_token()

    unique_id = uuid4().hex[:8]

    response = client.post(
        "/devices/",
        json={
            "name": f"pytest-device-{unique_id}",
            "ip_address": f"10.20.{int(unique_id[:2],16)}.{int(unique_id[2:4],16)}",
            "hostname": f"host-{unique_id}",
            "device_type": "router",
            "location": "pytest-lab",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == f"pytest-device-{unique_id}"


def test_get_device():
    token = get_admin_token()

    unique_id = uuid4().hex[:8]

    create_response = client.post(
        "/devices/",
        json={
            "name": f"get-device-{unique_id}",
            "ip_address": f"10.21.{int(unique_id[:2],16)}.{int(unique_id[2:4],16)}",
            "hostname": f"host-{unique_id}",
            "device_type": "switch",
            "location": "pytest-lab",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert create_response.status_code == 200

    device_id = create_response.json()["id"]

    response = client.get(
        f"/devices/{device_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == device_id


def test_update_device():
    token = get_admin_token()

    unique_id = uuid4().hex[:8]

    create_response = client.post(
        "/devices/",
        json={
            "name": f"update-device-{unique_id}",
            "ip_address": f"10.22.{int(unique_id[:2],16)}.{int(unique_id[2:4],16)}",
            "hostname": f"host-{unique_id}",
            "device_type": "router",
            "location": "pytest-lab",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert create_response.status_code == 200

    device_id = create_response.json()["id"]

    response = client.put(
        f"/devices/{device_id}",
        json={
            "name": f"updated-device-{unique_id}"
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == f"updated-device-{unique_id}"


def test_delete_device():
    token = get_admin_token()

    unique_id = uuid4().hex[:8]

    create_response = client.post(
        "/devices/",
        json={
            "name": f"delete-device-{unique_id}",
            "ip_address": f"10.23.{int(unique_id[:2],16)}.{int(unique_id[2:4],16)}",
            "hostname": f"host-{unique_id}",
            "device_type": "router",
            "location": "pytest-lab",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert create_response.status_code == 200

    device_id = create_response.json()["id"]

    response = client.delete(
        f"/devices/{device_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code in [200, 204]


def test_devices_requires_auth():
    response = client.get("/devices/")

    assert response.status_code in [401, 403]