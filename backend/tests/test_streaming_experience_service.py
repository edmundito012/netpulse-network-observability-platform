from app.services.streaming_experience_service import (
    StreamingExperienceService,
)


def test_excellent_streaming():

    result = (
        StreamingExperienceService.analyze(
            latency_ms=20,
            jitter_ms=5,
            packet_loss_percent=0,
        )
    )

    assert result.streaming_score >= 90
    assert result.quality == "EXCELLENT"


def test_poor_streaming():

    result = (
        StreamingExperienceService.analyze(
            latency_ms=180,
            jitter_ms=45,
            packet_loss_percent=8,
        )
    )

    assert result.quality == "POOR"