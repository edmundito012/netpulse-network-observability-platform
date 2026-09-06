from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.main import app
from app.models.user import User, UserRole

client = TestClient(app)


def create_test_admin():
    db = SessionLocal()

    email = f"admin_{uuid4().hex}@test.com"
    username = f"admin_{uuid4().hex}"

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


def test_list_users():
    token = get_admin_token()

    response = client.get(
        "/users/",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_user():
    token = get_admin_token()

    unique_id = uuid4().hex

    response = client.post(
        "/users/",
        json={
            "email": f"pytest_user_{unique_id}@test.com",
            "username": f"pytest_user_{unique_id}",
            "password": "pytest123",
            "role": "VIEWER",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 201


def test_get_user():
    token = get_admin_token()

    users_response = client.get(
        "/users/",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert users_response.status_code == 200

    users = users_response.json()

    assert len(users) > 0

    user_id = users[0]["id"]

    response = client.get(
        f"/users/{user_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200


def test_update_user():
    token = get_admin_token()

    unique_id = uuid4().hex

    create_response = client.post(
        "/users/",
        json={
            "email": f"update_user_{unique_id}@test.com",
            "username": f"update_user_{unique_id}",
            "password": "pytest123",
            "role": "VIEWER",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert create_response.status_code == 201

    user_id = create_response.json()["id"]

    response = client.put(
        f"/users/{user_id}",
        json={
            "username": f"updated_user_{unique_id}",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["username"] == f"updated_user_{unique_id}"


def test_users_requires_auth():
    response = client.get("/users/")

    assert response.status_code in [401, 403]
