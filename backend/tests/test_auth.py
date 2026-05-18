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