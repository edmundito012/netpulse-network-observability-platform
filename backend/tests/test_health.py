from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data

    assert data["status"] in [
        "ok",
        "degraded",
    ]

    assert "database" in data
    assert "scheduler_running" in data