from dataclasses import dataclass


@dataclass
class NetworkHealthScoreResult:
    health_score: int

    grade: str

    latency_score: int
    jitter_score: int
    packet_loss_score: int
    stability_score: int

    bottleneck: str

    recommendation: str


class NetworkHealthScoreService:

    @staticmethod
    def latency_score(latency: float) -> int:

        if latency <= 20:
            return 100

        if latency <= 40:
            return 90

        if latency <= 70:
            return 75

        if latency <= 120:
            return 55

        return 25

    @staticmethod
    def jitter_score(jitter: float) -> int:

        if jitter <= 5:
            return 100

        if jitter <= 10:
            return 90

        if jitter <= 20:
            return 75

        if jitter <= 30:
            return 50

        return 20

    @staticmethod
    def packet_loss_score(loss: float) -> int:

        if loss == 0:
            return 100

        if loss <= 0.5:
            return 90

        if loss <= 1:
            return 75

        if loss <= 3:
            return 50

        return 20

    @staticmethod
    def grade(score: int) -> str:

        if score >= 95:
            return "A+"

        if score >= 90:
            return "A"

        if score >= 80:
            return "B"

        if score >= 70:
            return "C"

        if score >= 60:
            return "D"

        return "F"

    @staticmethod
    def analyze(
        latency_score: int,
        jitter_score: int,
        packet_loss_score: int,
        stability_score: int,
    ):

        health = round(
            (
                latency_score * 0.35
                + jitter_score * 0.25
                + packet_loss_score * 0.25
                + stability_score * 0.15
            )
        )

        values = {
            "latency": latency_score,
            "jitter": jitter_score,
            "packet_loss": packet_loss_score,
            "stability": stability_score,
        }

        bottleneck = min(
            values,
            key=values.get,
        )

        if health >= 90:
            recommendation = (
                "Network is operating at an excellent level."
            )
        elif health >= 75:
            recommendation = (
                "Minor degradation detected."
            )
        else:
            recommendation = (
                f"Improve {bottleneck} to increase overall health."
            )

        return NetworkHealthScoreResult(
            health_score=health,
            grade=(
                NetworkHealthScoreService.grade(
                    health,
                )
            ),
            latency_score=latency_score,
            jitter_score=jitter_score,
            packet_loss_score=packet_loss_score,
            stability_score=stability_score,
            bottleneck=bottleneck,
            recommendation=recommendation,
        )