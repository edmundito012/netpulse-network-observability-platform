from dataclasses import dataclass


@dataclass
class NetworkImpactResult:
    impact_score: int
    status: str
    affected_services: list[str]
    message: str


class NetworkImpactService:

    @staticmethod
    def calculate_status(score: int) -> str:
        if score >= 81:
            return "CRITICAL"

        if score >= 61:
            return "DEGRADED"

        if score >= 31:
            return "WARNING"

        return "HEALTHY"

    @staticmethod
    def calculate_impact(
        latency_ms: float,
        packet_loss_percent: float,
        jitter_ms: float,
        failure_risk: int,
    ) -> NetworkImpactResult:

        latency_score = min(100, latency_ms / 2)
        packet_loss_score = min(100, packet_loss_percent * 4)
        jitter_score = min(100, jitter_ms * 2)

        impact_score = min(
            100,
            int(
                latency_score * 0.25
                + packet_loss_score * 0.30
                + jitter_score * 0.25
                + failure_risk * 0.20
            ),
        )

        affected_services = []

        if jitter_ms >= 40:
            affected_services.extend(
                ["video_calls", "voip", "gaming"]
            )

        if packet_loss_percent >= 10:
            affected_services.extend(
                ["gaming", "video_calls", "voip", "vpn"]
            )

        if latency_ms >= 150:
            affected_services.extend(
                ["gaming", "video_calls", "vpn"]
            )

        if failure_risk >= 60:
            affected_services.extend(
                ["business_apps", "saas", "vpn"]
            )

        affected_services = sorted(set(affected_services))

        status = NetworkImpactService.calculate_status(
            impact_score
        )

        message = NetworkImpactService.build_message(
            status=status,
            affected_services=affected_services,
        )

        return NetworkImpactResult(
            impact_score=impact_score,
            status=status,
            affected_services=affected_services,
            message=message,
        )

    @staticmethod
    def build_message(
        status: str,
        affected_services: list[str],
    ) -> str:

        if status == "HEALTHY":
            return "Network operating normally."

        if status == "WARNING":
            return (
                "Minor network degradation detected."
            )

        if status == "DEGRADED":
            return (
                "Users may experience lag spikes and unstable calls."
            )

        return (
            "Critical network degradation detected. "
            "Business services may be impacted."
        )