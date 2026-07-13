from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_sla_endpoint():
    response = client.get(
        "/analytics/sla"
    )

    assert response.status_code == 200

    data = response.json()

    assert "samples_analyzed" in data
    assert "availability_percent" in data
    assert "latency_compliance_percent" in data
    assert "packet_loss_compliance_percent" in data
    assert "jitter_compliance_percent" in data
    assert "overall_compliance_percent" in data
    assert "status" in data
    assert "breached_metrics" in data