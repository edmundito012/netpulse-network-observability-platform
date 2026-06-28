from fastapi.testclient import (
    TestClient,
)

from app.main import app

client = TestClient(app)


def test_notification_history():

    response = client.get(
        "/notifications/history"
    )

    assert (
        response.status_code == 200
    )