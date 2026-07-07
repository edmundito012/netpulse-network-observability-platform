from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_video_call_endpoint():

    response = client.get(
        "/video-calls/experience"
    )

    assert response.status_code == 200

    data = response.json()

    assert "video_call_score" in data
    assert "zoom_ready" in data