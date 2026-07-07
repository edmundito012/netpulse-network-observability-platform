from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_network_health_api():

    response = client.get(
        "/analytics/health-score"
    )

    assert response.status_code == 200

    data = response.json()

    assert "health_score" in data
    assert "grade" in data