from dataclasses import dataclass


@dataclass
class NetworkRiskResult:
    risk_score: int
    risk_level: str
    failure_probability: int
    contributing_factors: list[str]


class NetworkRiskService:

    @staticmethod
    def classify_risk_level(score: int) -> str:
        if score >= 75:
            return "HIGH"

        if score >= 50:
            return "MEDIUM"

        return "LOW"

    @staticmethod
    def calculate(
        failure_risk: int,
        network_impact: int,
        predictive_alerts: int,
        network_health_score: int,
    ) -> NetworkRiskResult:
        health_risk = 100 - network_health_score
        predictive_risk = min(100, predictive_alerts * 20)

        risk_score = int(
            failure_risk * 0.35
            + network_impact * 0.25
            + predictive_risk * 0.20
            + health_risk * 0.20
        )

        contributing_factors = []

        if failure_risk >= 50:
            contributing_factors.append("failure_risk")

        if network_impact >= 50:
            contributing_factors.append("network_impact")

        if predictive_alerts > 0:
            contributing_factors.append("predictive_alerts")

        if health_risk >= 30:
            contributing_factors.append("health_score_degradation")

        return NetworkRiskResult(
            risk_score=risk_score,
            risk_level=NetworkRiskService.classify_risk_level(
                risk_score
            ),
            failure_probability=failure_risk,
            contributing_factors=contributing_factors,
        )