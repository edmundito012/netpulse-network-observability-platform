from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.device_metric import DeviceMetric
from app.repositories.device_metric_repository import (
    DeviceMetricRepository,
)
from app.schemas.gaming_experience import (
    GamingExperienceResponse,
)
from app.services.gaming_experience_service import (
    GamingExperienceService,
)
from app.services.latency_intelligence_service import (
    LatencyIntelligenceService,
)

router = APIRouter(
    prefix="/gaming",
    tags=["Gaming Experience"],
)


@router.get(
    "/experience",
    response_model=GamingExperienceResponse,
)
def get_gaming_experience(
    device_id: int | None = None,
    db: Session = Depends(get_db),
):
    if device_id is None:
        metrics = (
            db.query(DeviceMetric)
            .order_by(DeviceMetric.checked_at.desc())
            .limit(10)
            .all()
        )
    else:
        metrics = DeviceMetricRepository.get_latest_metrics(
            db=db,
            device_id=device_id,
            limit=10,
        )

    if not metrics:
        result = GamingExperienceService.analyze(
            latency_ms=0,
            jitter_ms=0,
            packet_loss_percent=0,
            latency_spread_ms=0,
            latency_spike_detected=False,
        )

        return GamingExperienceResponse(**result.__dict__)

    latencies = [
        metric.response_time_ms or 0
        for metric in metrics
    ]

    latency_intelligence = LatencyIntelligenceService.analyze(
        latencies=latencies,
    )

    latest_metric = metrics[0]

    result = GamingExperienceService.analyze(
        latency_ms=latest_metric.response_time_ms or 0,
        jitter_ms=latest_metric.jitter_ms or 0,
        packet_loss_percent=latest_metric.packet_loss_percent or 0,
        latency_spread_ms=latency_intelligence.latency_spread_ms,
        latency_spike_detected=(
            latency_intelligence.latency_spike_detected
        ),
    )

    return GamingExperienceResponse(**result.__dict__)