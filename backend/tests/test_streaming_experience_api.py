from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_streaming_endpoint():

    response = client.get(
        "/streaming/experience"
    )

    assert response.status_code == 200

    data = response.json()

    assert "streaming_score" in data
    assert "quality" in data
    assert "recommended_resolution" in data