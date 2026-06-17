from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_top_risk_devices():

    response = client.get(
        "/devices/top-risk"
    )

    assert response.status_code in [
        200,
        401,
        403,
    ]

    if response.status_code == 200:

        data = response.json()

        assert isinstance(
            data,
            list,
        )