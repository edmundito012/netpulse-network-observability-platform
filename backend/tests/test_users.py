from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get_admin_token():
    response = client.post(
        "/auth/login",
        data={
            "username": "admin@netpulse.com",
            "password": "admin123",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def test_list_users():
    token = get_admin_token()

    response = client.get(
        "/users/",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200


def test_create_user():
    token = get_admin_token()

    response = client.post(
        "/users/",
        json={
            "email": "pytest_user@test.com",
            "username": "pytest_user",
            "password": "pytest123",
            "role": "VIEWER",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code in [201, 400]


def test_get_user():
    token = get_admin_token()

    response = client.get(
        "/users/1",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code in [200, 404]


def test_update_user():
    token = get_admin_token()

    response = client.put(
        "/users/1",
        json={
            "username": "updated_user"
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code in [200, 404]


def test_users_requires_auth():
    response = client.get("/users/")

    assert response.status_code in [401, 403]