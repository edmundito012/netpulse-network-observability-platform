from dataclasses import dataclass


@dataclass
class GamingExperienceResult:
    gaming_score: int
    competitive_ready: bool
    ping_stability: str
    lag_spike_risk: str
    rubber_banding_risk: str
    hit_registration: str
    recommended_games: list[str]
    recommendation: str


class GamingExperienceService:

    @staticmethod
    def classify_ping_stability(
        latency_spread_ms: float,
    ) -> str:
        if latency_spread_ms >= 80:
            return "POOR"

        if latency_spread_ms >= 40:
            return "FAIR"

        if latency_spread_ms >= 20:
            return "GOOD"

        return "EXCELLENT"

    @staticmethod
    def classify_lag_spike_risk(
        latency_spike_detected: bool,
        latency_spread_ms: float,
    ) -> str:
        if latency_spike_detected and latency_spread_ms >= 100:
            return "HIGH"

        if latency_spike_detected:
            return "MEDIUM"

        return "LOW"

    @staticmethod
    def classify_rubber_banding_risk(
        jitter_ms: float,
        packet_loss_percent: float,
        latency_spread_ms: float,
    ) -> str:
        if (
            packet_loss_percent >= 10
            or jitter_ms >= 50
            or latency_spread_ms >= 120
        ):
            return "CRITICAL"

        if (
            packet_loss_percent >= 5
            or jitter_ms >= 30
            or latency_spread_ms >= 80
        ):
            return "HIGH"

        if (
            packet_loss_percent >= 1
            or jitter_ms >= 15
            or latency_spread_ms >= 40
        ):
            return "MEDIUM"

        return "LOW"

    @staticmethod
    def classify_hit_registration(
        latency_ms: float,
        jitter_ms: float,
        packet_loss_percent: float,
    ) -> str:
        if (
            latency_ms <= 40
            and jitter_ms <= 10
            and packet_loss_percent < 1
        ):
            return "EXCELLENT"

        if (
            latency_ms <= 70
            and jitter_ms <= 20
            and packet_loss_percent < 3
        ):
            return "GOOD"

        if (
            latency_ms <= 100
            and jitter_ms <= 30
            and packet_loss_percent < 5
        ):
            return "FAIR"

        return "POOR"

    @staticmethod
    def calculate_score(
        latency_ms: float,
        jitter_ms: float,
        packet_loss_percent: float,
        latency_spread_ms: float,
        latency_spike_detected: bool,
    ) -> int:
        score = 100

        if latency_ms > 100:
            score -= 30
        elif latency_ms > 70:
            score -= 20
        elif latency_ms > 40:
            score -= 10

        if jitter_ms > 30:
            score -= 25
        elif jitter_ms > 15:
            score -= 15
        elif jitter_ms > 10:
            score -= 5

        if packet_loss_percent >= 5:
            score -= 30
        elif packet_loss_percent >= 1:
            score -= 15

        if latency_spread_ms >= 80:
            score -= 20
        elif latency_spread_ms >= 40:
            score -= 10

        if latency_spike_detected:
            score -= 10

        return max(0, min(100, int(score)))

    @staticmethod
    def build_recommendation(
        gaming_score: int,
        competitive_ready: bool,
        rubber_banding_risk: str,
    ) -> str:
        if competitive_ready:
            return "Excellent for competitive gaming."

        if rubber_banding_risk in ["HIGH", "CRITICAL"]:
            return (
                "High risk of rubber banding. "
                "Investigate jitter, packet loss, and WAN stability."
            )

        if gaming_score >= 70:
            return "Good for casual gaming, but not ideal for competitive play."

        return "Poor gaming experience expected. Check latency, jitter, and packet loss."

    @staticmethod
    def recommend_games(
        gaming_score: int,
        competitive_ready: bool,
    ) -> list[str]:
        if competitive_ready:
            return [
                "CS2",
                "Valorant",
                "Rocket League",
                "Fortnite",
            ]

        if gaming_score >= 70:
            return [
                "Minecraft",
                "EA FC",
                "GTA Online",
            ]

        return [
            "Turn-based games",
            "Single-player games",
        ]

    @staticmethod
    def analyze(
        latency_ms: float,
        jitter_ms: float,
        packet_loss_percent: float,
        latency_spread_ms: float,
        latency_spike_detected: bool,
    ) -> GamingExperienceResult:
        gaming_score = GamingExperienceService.calculate_score(
            latency_ms=latency_ms,
            jitter_ms=jitter_ms,
            packet_loss_percent=packet_loss_percent,
            latency_spread_ms=latency_spread_ms,
            latency_spike_detected=latency_spike_detected,
        )

        ping_stability = GamingExperienceService.classify_ping_stability(
            latency_spread_ms=latency_spread_ms,
        )

        lag_spike_risk = GamingExperienceService.classify_lag_spike_risk(
            latency_spike_detected=latency_spike_detected,
            latency_spread_ms=latency_spread_ms,
        )

        rubber_banding_risk = (
            GamingExperienceService.classify_rubber_banding_risk(
                jitter_ms=jitter_ms,
                packet_loss_percent=packet_loss_percent,
                latency_spread_ms=latency_spread_ms,
            )
        )

        hit_registration = GamingExperienceService.classify_hit_registration(
            latency_ms=latency_ms,
            jitter_ms=jitter_ms,
            packet_loss_percent=packet_loss_percent,
        )

        competitive_ready = (
            gaming_score >= 85
            and ping_stability in ["EXCELLENT", "GOOD"]
            and lag_spike_risk == "LOW"
            and rubber_banding_risk == "LOW"
            and hit_registration in ["EXCELLENT", "GOOD"]
        )

        recommended_games = GamingExperienceService.recommend_games(
            gaming_score=gaming_score,
            competitive_ready=competitive_ready,
        )

        recommendation = GamingExperienceService.build_recommendation(
            gaming_score=gaming_score,
            competitive_ready=competitive_ready,
            rubber_banding_risk=rubber_banding_risk,
        )

        return GamingExperienceResult(
            gaming_score=gaming_score,
            competitive_ready=competitive_ready,
            ping_stability=ping_stability,
            lag_spike_risk=lag_spike_risk,
            rubber_banding_risk=rubber_banding_risk,
            hit_registration=hit_registration,
            recommended_games=recommended_games,
            recommendation=recommendation,
        )