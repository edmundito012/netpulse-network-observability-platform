from dataclasses import dataclass


@dataclass
class GamingImpactResult:
    impact_score: int
    status: str
    gaming_quality: str
    lag_risk: str
    packet_loss_risk: str
    jitter_risk: str
    recommended_action: str


class GamingImpactService:

    @staticmethod
    def classify_lag_risk(latency: float) -> str:
        if latency > 100:
            return "HIGH"

        if latency >= 50:
            return "MEDIUM"

        return "LOW"

    @staticmethod
    def classify_packet_loss_risk(
        packet_loss: float,
    ) -> str:
        if packet_loss > 5:
            return "HIGH"

        if packet_loss >= 1:
            return "MEDIUM"

        return "LOW"

    @staticmethod
    def classify_jitter_risk(
        jitter: float,
    ) -> str:
        if jitter > 30:
            return "HIGH"

        if jitter >= 10:
            return "MEDIUM"

        return "LOW"

    @staticmethod
    def classify_gaming_quality(
        latency: float,
        packet_loss: float,
        jitter: float,
    ) -> str:
        if (
            latency > 100
            or packet_loss > 5
            or jitter > 30
        ):
            return "POOR"

        if (
            latency >= 50
            or packet_loss >= 1
            or jitter >= 10
        ):
            return "FAIR"

        return "GOOD"

    @staticmethod
    def build_recommendation(
        latency: float,
        packet_loss: float,
        jitter: float,
    ) -> str:
        if packet_loss > 5:
            return "Inspect WAN links."

        if jitter > 30:
            return "Check ISP stability."

        if latency > 100:
            return "Investigate routing path."

        return "Network suitable for gaming."

    @staticmethod
    def calculate_gaming_impact(
        impact_score: int,
        status: str,
        latency: float,
        packet_loss: float,
        jitter: float,
    ) -> GamingImpactResult:
        gaming_quality = GamingImpactService.classify_gaming_quality(
            latency=latency,
            packet_loss=packet_loss,
            jitter=jitter,
        )

        lag_risk = GamingImpactService.classify_lag_risk(
            latency=latency,
        )

        packet_loss_risk = GamingImpactService.classify_packet_loss_risk(
            packet_loss=packet_loss,
        )

        jitter_risk = GamingImpactService.classify_jitter_risk(
            jitter=jitter,
        )

        recommended_action = GamingImpactService.build_recommendation(
            latency=latency,
            packet_loss=packet_loss,
            jitter=jitter,
        )

        return GamingImpactResult(
            impact_score=impact_score,
            status=status,
            gaming_quality=gaming_quality,
            lag_risk=lag_risk,
            packet_loss_risk=packet_loss_risk,
            jitter_risk=jitter_risk,
            recommended_action=recommended_action,
        )