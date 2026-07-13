from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_portfolio_dashboard():
    response = client.get(
        "/portfolio"
    )

    assert response.status_code == 200

    assert "NetPulse" in response.text

    assert (
        "Network Observability"
        in response.text
    )

    assert (
        "Gaming Experience"
        in response.text
    )

    assert (
        "Streaming Experience"
        in response.text
    )