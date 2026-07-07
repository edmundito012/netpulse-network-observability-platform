from fastapi import APIRouter

from app.schemas.network_health_score import (
    NetworkHealthScoreResponse,
)

from app.services.network_health_score_service import (
    NetworkHealthScoreService,
)

router = APIRouter(
    prefix="/analytics",
    tags=["Network Analytics"],
)


@router.get(
    "/health-score",
    response_model=NetworkHealthScoreResponse,
)
def get_health_score():

    latency = (
        NetworkHealthScoreService
        .latency_score(22)
    )

    jitter = (
        NetworkHealthScoreService
        .jitter_score(6)
    )

    loss = (
        NetworkHealthScoreService
        .packet_loss_score(0)
    )

    result = (
        NetworkHealthScoreService
        .analyze(
            latency_score=latency,
            jitter_score=jitter,
            packet_loss_score=loss,
            stability_score=95,
        )
    )

    return NetworkHealthScoreResponse(
        **result.__dict__
    )