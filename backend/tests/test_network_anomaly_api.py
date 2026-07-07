from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_network_anomalies_api():

    response = client.get(
        "/analytics/network-anomalies"
    )

    assert response.status_code == 200

    data = response.json()

    assert "metric_name" in data
    assert "z_score" in data
    assert "severity" in data
    assert "anomaly_detected" in data