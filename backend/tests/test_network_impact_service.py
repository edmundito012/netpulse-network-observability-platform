from app.services.network_impact_service import (
    NetworkImpactService,
)


def test_network_impact_healthy():

    result = NetworkImpactService.calculate_impact(
        latency_ms=10,
        packet_loss_percent=0,
        jitter_ms=5,
        failure_risk=0,
    )

    assert result.status == "HEALTHY"
    assert result.impact_score < 31

def test_network_impact_degraded():

    result = NetworkImpactService.calculate_impact(
        latency_ms=180,
        packet_loss_percent=15,
        jitter_ms=50,
        failure_risk=40,
    )

    assert result.status in [
        "WARNING",
        "DEGRADED",
        "CRITICAL",
    ]

    assert "gaming" in result.affected_services


def test_network_impact_critical():

    result = NetworkImpactService.calculate_impact(
        latency_ms=300,
        packet_loss_percent=30,
        jitter_ms=80,
        failure_risk=90,
    )

    assert result.status == "CRITICAL"
    assert result.impact_score > 80