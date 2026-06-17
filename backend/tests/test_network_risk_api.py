from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_network_risk_endpoint():
    response = client.get("/network/risk")

    assert response.status_code == 200

    data = response.json()

    assert "risk_score" in data
    assert "risk_level" in data
    assert "failure_probability" in data
    assert "contributing_factors" in data