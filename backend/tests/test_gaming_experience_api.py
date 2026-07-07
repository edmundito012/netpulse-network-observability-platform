from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_gaming_experience_endpoint():
    response = client.get("/gaming/experience")

    assert response.status_code == 200

    data = response.json()

    assert "gaming_score" in data
    assert "competitive_ready" in data
    assert "ping_stability" in data
    assert "rubber_banding_risk" in data
    assert "hit_registration" in data