from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_admin_only_requires_auth():
    response = client.get("/auth/admin-only")

    assert response.status_code == 401


def test_operator_only_requires_auth():
    response = client.get("/auth/operator-only")

    assert response.status_code == 401


def test_viewer_or_above_requires_auth():
    response = client.get("/auth/viewer-or-above")

    assert response.status_code == 401