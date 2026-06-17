from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_device_risk_ranking():

    response = client.get(
        "/devices/risk-ranking"
    )

    assert response.status_code in [200, 401, 403]

    if response.status_code == 200:
        data = response.json()

        assert isinstance(data, list)
        assert len(data) > 0

        assert "risk_score" in data[0]
        assert "risk_level" in data[0]