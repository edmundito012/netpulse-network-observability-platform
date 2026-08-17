from fastapi.testclient import TestClient

from app.api import health as health_api
from app.main import app

client = TestClient(app)


def test_legacy_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] in [
        "ok",
        "degraded",
    ]
    assert "database" in data
    assert "scheduler_running" in data
    assert "dashboard_cache_loaded" in data
    assert "device_state_cache_count" in data


def test_liveness_probe():
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "alive",
    }


def test_readiness_probe_when_database_is_available(
    monkeypatch,
):
    monkeypatch.setattr(
        health_api,
        "get_database_status",
        lambda: "ok",
    )

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "ok",
    }


def test_readiness_probe_when_database_is_unavailable(
    monkeypatch,
):
    monkeypatch.setattr(
        health_api,
        "get_database_status",
        lambda: "error",
    )

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "database": "error",
    }


def test_startup_probe_before_initialization():
    original_value = app.state.startup_complete
    app.state.startup_complete = False

    try:
        response = client.get("/health/startup")
    finally:
        app.state.startup_complete = original_value

    assert response.status_code == 503
    assert response.json() == {
        "status": "starting",
    }


def test_startup_probe_after_initialization():
    original_value = app.state.startup_complete
    app.state.startup_complete = True

    try:
        response = client.get("/health/startup")
    finally:
        app.state.startup_complete = original_value

    assert response.status_code == 200
    assert response.json() == {
        "status": "started",
    }
