from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_network_impact_endpoint():

    response = client.get("/network/impact")

    assert response.status_code == 200

    data = response.json()

    assert "impact_score" in data
    assert "status" in data
    assert "affected_services" in data

def test_network_impact_contains_summary():
    response = client.get("/network/impact")

    assert response.status_code == 200

    data = response.json()

    assert "average_latency_ms" in data
    assert "average_packet_loss_percent" in data
    assert "average_jitter_ms" in data