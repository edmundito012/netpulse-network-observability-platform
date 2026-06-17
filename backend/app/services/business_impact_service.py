from dataclasses import dataclass


@dataclass
class BusinessImpactResult:
    impact_score: int
    status: str

    teams_quality: str
    zoom_quality: str
    voip_quality: str
    vpn_quality: str


class BusinessImpactService:

    @staticmethod
    def classify_quality(
        latency: float,
        packet_loss: float,
        jitter: float,
    ) -> str:

        if (
            latency >= 150
            or packet_loss >= 10
            or jitter >= 40
        ):
            return "POOR"

        if (
            latency >= 80
            or packet_loss >= 3
            or jitter >= 20
        ):
            return "FAIR"

        return "GOOD"

    @staticmethod
    def calculate_business_impact(
        impact_score: int,
        status: str,
        latency: float,
        packet_loss: float,
        jitter: float,
    ) -> BusinessImpactResult:

        quality = BusinessImpactService.classify_quality(
            latency,
            packet_loss,
            jitter,
        )

        return BusinessImpactResult(
            impact_score=impact_score,
            status=status,
            teams_quality=quality,
            zoom_quality=quality,
            voip_quality=quality,
            vpn_quality=quality,
        )