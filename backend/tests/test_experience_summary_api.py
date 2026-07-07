from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_summary_api():

    response = client.get(
        "/experience/summary"
    )

    assert response.status_code == 200

    data = response.json()

    assert "overall_qoe_score" in data
    assert "gaming" in data
    assert "streaming" in data