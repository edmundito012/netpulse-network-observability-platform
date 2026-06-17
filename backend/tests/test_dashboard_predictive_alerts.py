from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_contains_predictive_fields():
    response = client.get("/dashboard/overview")

    assert response.status_code in [200, 401, 403]

    if response.status_code == 200:
        data = response.json()

        assert "predictive_alerts" in data
        assert "devices_with_predictive_risk" in data