from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_gaming_impact_endpoint():

    response = client.get(
        "/network/impact/gaming"
    )

    assert response.status_code == 200

    data = response.json()

    assert "gaming_quality" in data
    assert "lag_risk" in data
    assert "packet_loss_risk" in data
    assert "jitter_risk" in data
    assert "recommended_action" in data