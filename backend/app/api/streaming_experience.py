from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.device_metric import DeviceMetric

from app.schemas.streaming_experience import (
    StreamingExperienceResponse,
)

from app.services.streaming_experience_service import (
    StreamingExperienceService,
)

router = APIRouter(
    prefix="/streaming",
    tags=["Streaming Experience"],
)


@router.get(
    "/experience",
    response_model=StreamingExperienceResponse,
)
def get_streaming_experience(
    db: Session = Depends(get_db),
):

    metric = (
        db.query(DeviceMetric)
        .order_by(
            DeviceMetric.checked_at.desc()
        )
        .first()
    )

    if metric is None:

        result = (
            StreamingExperienceService.analyze(
                latency_ms=0,
                jitter_ms=0,
                packet_loss_percent=0,
            )
        )

        return StreamingExperienceResponse(
            **result.__dict__
        )

    result = (
        StreamingExperienceService.analyze(
            latency_ms=metric.response_time_ms or 0,
            jitter_ms=metric.jitter_ms or 0,
            packet_loss_percent=(
                metric.packet_loss_percent or 0
            ),
        )
    )

    return StreamingExperienceResponse(
        **result.__dict__
    )