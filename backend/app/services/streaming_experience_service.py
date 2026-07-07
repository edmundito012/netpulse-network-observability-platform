from dataclasses import dataclass


@dataclass
class StreamingExperienceResult:
    streaming_score: int
    quality: str
    recommended_resolution: str
    buffering_risk: str
    live_stream_ready: bool
    recommended_platforms: list[str]
    recommendation: str


class StreamingExperienceService:

    @staticmethod
    def calculate_score(
        latency_ms: float,
        jitter_ms: float,
        packet_loss_percent: float,
    ) -> int:

        score = 100

        if latency_ms > 150:
            score -= 25
        elif latency_ms > 80:
            score -= 15
        elif latency_ms > 40:
            score -= 5

        if jitter_ms > 30:
            score -= 20
        elif jitter_ms > 15:
            score -= 10

        if packet_loss_percent > 5:
            score -= 40
        elif packet_loss_percent > 2:
            score -= 20
        elif packet_loss_percent > 0:
            score -= 5

        return max(0, min(score, 100))

    @staticmethod
    def classify_quality(
        score: int,
    ) -> str:

        if score >= 90:
            return "EXCELLENT"

        if score >= 75:
            return "GOOD"

        if score >= 60:
            return "FAIR"

        return "POOR"

    @staticmethod
    def recommended_resolution(
        score: int,
    ) -> str:

        if score >= 95:
            return "4K"

        if score >= 80:
            return "1440p"

        if score >= 70:
            return "1080p"

        if score >= 60:
            return "720p"

        return "480p"

    @staticmethod
    def buffering_risk(
        packet_loss_percent: float,
        jitter_ms: float,
    ) -> str:

        if (
            packet_loss_percent >= 5
            or jitter_ms >= 40
        ):
            return "HIGH"

        if (
            packet_loss_percent >= 2
            or jitter_ms >= 20
        ):
            return "MEDIUM"

        return "LOW"

    @staticmethod
    def live_stream_ready(
        latency_ms: float,
        jitter_ms: float,
        packet_loss_percent: float,
    ) -> bool:

        return (
            latency_ms < 50
            and jitter_ms < 15
            and packet_loss_percent < 1
        )

    @staticmethod
    def recommendation(
        quality: str,
    ) -> str:

        if quality == "EXCELLENT":
            return (
                "Excellent for Netflix, YouTube "
                "and Twitch streaming."
            )

        if quality == "GOOD":
            return (
                "Good for HD streaming."
            )

        if quality == "FAIR":
            return (
                "Occasional buffering may occur."
            )

        return (
            "Streaming quality may be poor."
        )

    @staticmethod
    def analyze(
        latency_ms: float,
        jitter_ms: float,
        packet_loss_percent: float,
    ) -> StreamingExperienceResult:

        score = (
            StreamingExperienceService.calculate_score(
                latency_ms,
                jitter_ms,
                packet_loss_percent,
            )
        )

        quality = (
            StreamingExperienceService.classify_quality(
                score
            )
        )

        return StreamingExperienceResult(
            streaming_score=score,
            quality=quality,
            recommended_resolution=(
                StreamingExperienceService
                .recommended_resolution(score)
            ),
            buffering_risk=(
                StreamingExperienceService
                .buffering_risk(
                    packet_loss_percent,
                    jitter_ms,
                )
            ),
            live_stream_ready=(
                StreamingExperienceService
                .live_stream_ready(
                    latency_ms,
                    jitter_ms,
                    packet_loss_percent,
                )
            ),
            recommended_platforms=[
                "Netflix",
                "YouTube",
                "Disney+",
                "Twitch",
            ],
            recommendation=(
                StreamingExperienceService
                .recommendation(
                    quality
                )
            ),
        )