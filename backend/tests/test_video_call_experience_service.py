from app.services.video_call_experience_service import (
    VideoCallExperienceService,
)


def test_video_call_quality():

    result = (
        VideoCallExperienceService.analyze(
            latency_ms=20,
            jitter_ms=5,
            packet_loss_percent=0,
        )
    )

    assert result.video_call_score >= 90
    assert result.zoom_ready is True