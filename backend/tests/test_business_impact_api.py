from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_business_impact_endpoint():

    response = client.get(
        "/network/impact/business"
    )

    assert response.status_code == 200

    data = response.json()

    assert "teams_quality" in data
    assert "zoom_quality" in data
    assert "voip_quality" in data
    assert "vpn_quality" in data