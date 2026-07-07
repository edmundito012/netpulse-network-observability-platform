from fastapi import APIRouter

from app.schemas.video_call_experience import (
    VideoCallExperienceResponse,
)

from app.services.video_call_experience_service import (
    VideoCallExperienceService,
)

router = APIRouter(
    prefix="/video-calls",
    tags=["Video Calls"],
)


@router.get(
    "/experience",
    response_model=VideoCallExperienceResponse,
)
def get_video_call_experience():

    result = (
        VideoCallExperienceService.analyze(
            latency_ms=30,
            jitter_ms=8,
            packet_loss_percent=0,
        )
    )

    return VideoCallExperienceResponse(
        **result.__dict__
    )