from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_network_quality_api():

    response = client.get(
        "/analytics/network-quality"
    )

    assert response.status_code == 200

    data = response.json()

    assert "average_latency" in data
    assert "p95_latency" in data
    assert "quality_grade" in data