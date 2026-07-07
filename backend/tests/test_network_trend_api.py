from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_network_trends_api():

    response = client.get(
        "/analytics/network-trends"
    )

    assert response.status_code == 200

    data = response.json()

    assert "trend" in data
    assert "slope" in data
    assert "predicted_next_latency" in data
    assert "recommendation" in data