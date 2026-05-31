from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.main import app
from app.models.user import User, UserRole


client = TestClient(app)


def create_test_admin():
    db = SessionLocal()

    email = f"audit_admin_{uuid4().hex}@test.com"
    username = f"audit_admin_{uuid4().hex}"

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


def test_audit_logs_requires_auth():
    response = client.get("/audit-logs/")

    assert response.status_code in [401, 403]


def test_list_audit_logs():
    token = get_admin_token()

    response = client.get(
        "/audit-logs/",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_user_generates_audit_log():
    token = get_admin_token()

    unique_id = uuid4().hex

    username = f"audit_pytest_user_{unique_id}"
    email = f"audit_pytest_{unique_id}@test.com"

    create_response = client.post(
        "/users/",
        json={
            "email": email,
            "username": username,
            "password": "pytest123",
            "role": "VIEWER",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert create_response.status_code == 201

    logs_response = client.get(
        "/audit-logs/",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert logs_response.status_code == 200

    logs = logs_response.json()

    assert isinstance(logs, list)
    assert len(logs) > 0

    matching_logs = [
        log for log in logs
        if log["action"] == "CREATE_USER"
        and log["resource_type"] == "USER"
        and log["details"]["email"] == email
    ]

    assert len(matching_logs) >= 1


def test_audit_logs_limit_parameter():
    token = get_admin_token()

    response = client.get(
        "/audit-logs/?limit=10",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    logs = response.json()

    assert isinstance(logs, list)
    assert len(logs) <= 10