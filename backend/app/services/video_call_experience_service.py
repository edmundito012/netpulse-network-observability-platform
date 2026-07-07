from dataclasses import dataclass


@dataclass
class VideoCallExperienceResult:
    video_call_score: int
    quality: str

    zoom_ready: bool
    teams_ready: bool
    meet_ready: bool
    discord_ready: bool

    audio_drop_risk: str
    video_freeze_risk: str

    recommendation: str


class VideoCallExperienceService:

    @staticmethod
    def calculate_score(
        latency_ms: float,
        jitter_ms: float,
        packet_loss_percent: float,
    ) -> int:

        score = 100

        if latency_ms > 120:
            score -= 25
        elif latency_ms > 70:
            score -= 15
        elif latency_ms > 40:
            score -= 5

        if jitter_ms > 30:
            score -= 30
        elif jitter_ms > 15:
            score -= 15

        if packet_loss_percent > 3:
            score -= 35
        elif packet_loss_percent > 1:
            score -= 15

        return max(0, min(score, 100))

    @staticmethod
    def quality(score):

        if score >= 90:
            return "EXCELLENT"

        if score >= 75:
            return "GOOD"

        if score >= 60:
            return "FAIR"

        return "POOR"

    @staticmethod
    def audio_drop_risk(
        jitter,
        packet_loss,
    ):

        if jitter >= 30 or packet_loss >= 3:
            return "HIGH"

        if jitter >= 15 or packet_loss >= 1:
            return "MEDIUM"

        return "LOW"

    @staticmethod
    def video_freeze_risk(
        latency,
        packet_loss,
    ):

        if latency >= 150 or packet_loss >= 5:
            return "HIGH"

        if latency >= 80 or packet_loss >= 2:
            return "MEDIUM"

        return "LOW"

    @staticmethod
    def analyze(
        latency_ms,
        jitter_ms,
        packet_loss_percent,
    ):

        score = (
            VideoCallExperienceService
            .calculate_score(
                latency_ms,
                jitter_ms,
                packet_loss_percent,
            )
        )

        quality = (
            VideoCallExperienceService
            .quality(score)
        )

        ready = score >= 80

        return VideoCallExperienceResult(
            video_call_score=score,

            quality=quality,

            zoom_ready=ready,

            teams_ready=ready,

            meet_ready=ready,

            discord_ready=ready,

            audio_drop_risk=(
                VideoCallExperienceService
                .audio_drop_risk(
                    jitter_ms,
                    packet_loss_percent,
                )
            ),

            video_freeze_risk=(
                VideoCallExperienceService
                .video_freeze_risk(
                    latency_ms,
                    packet_loss_percent,
                )
            ),

            recommendation=(
                "Excellent for HD video conferencing."
                if ready
                else
                "Network quality may affect video meetings."
            ),
        )