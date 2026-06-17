from app.services.network_risk_service import NetworkRiskService


def test_network_risk_low():
    result = NetworkRiskService.calculate(
        failure_risk=10,
        network_impact=10,
        predictive_alerts=0,
        network_health_score=90,
    )

    assert result.risk_level == "LOW"


def test_network_risk_high():
    result = NetworkRiskService.calculate(
        failure_risk=90,
        network_impact=90,
        predictive_alerts=3,
        network_health_score=40,
    )

    assert result.risk_level == "HIGH"
    assert "failure_risk" in result.contributing_factors