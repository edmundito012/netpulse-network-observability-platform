from fastapi import APIRouter

from app.schemas.experience_summary import (
    ExperienceSummaryResponse,
    ExperienceProfile,
)

from app.services.experience_summary_service import (
    ExperienceSummaryService,
)

router = APIRouter(
    prefix="/experience",
    tags=["Experience"],
)


@router.get(
    "/summary",
    response_model=ExperienceSummaryResponse,
)
def get_summary():

    result = (
        ExperienceSummaryService.build(
            gaming_score=95,
            streaming_score=92,
        )
    )

    return ExperienceSummaryResponse(

        overall_qoe_score=result.overall_qoe_score,

        overall_status=result.overall_status,

        gaming=ExperienceProfile(
            score=result.gaming.score,
            status=result.gaming.status,
        ),

        streaming=ExperienceProfile(
            score=result.streaming.score,
            status=result.streaming.status,
        ),

        recommendation=result.recommendation,
    )