from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_login_invalid_credentials():
    response = client.post(
        "/auth/login",
        data={
            "username": "fake@test.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401


def test_me_requires_auth():
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_public_registration_creates_viewer():
    unique_id = uuid4().hex

    response = client.post(
        "/auth/register",
        json={
            "email": f"registered_{unique_id}@test.com",
            "username": f"registered_{unique_id}",
            "password": "secure-password",
        },
    )

    assert response.status_code == 200
    assert response.json()["role"] == "VIEWER"


@pytest.mark.parametrize(
    "requested_role",
    [
        "ADMIN",
        "OPERATOR",
    ],
)
def test_public_registration_rejects_role_assignment(requested_role):
    unique_id = uuid4().hex

    response = client.post(
        "/auth/register",
        json={
            "email": f"escalation_{unique_id}@test.com",
            "username": f"escalation_{unique_id}",
            "password": "secure-password",
            "role": requested_role,
        },
    )

    assert response.status_code == 422
    assert any(
        error["loc"][-1] == "role" and error["type"] == "extra_forbidden"
        for error in response.json()["detail"]
    )
