from fastapi import APIRouter

from app.schemas.network_quality import (
    NetworkQualityResponse,
)

from app.services.network_quality_service import (
    NetworkQualityService,
)

router = APIRouter(
    prefix="/analytics",
    tags=["Network Analytics"],
)


@router.get(
    "/network-quality",
    response_model=NetworkQualityResponse,
)
def network_quality():

    latencies = [
        20,
        22,
        21,
        23,
        19,
        21,
        22,
        20,
        21,
        20,
    ]

    result = (
        NetworkQualityService.analyze(
            latencies
        )
    )

    return NetworkQualityResponse(
        **result.__dict__
    )