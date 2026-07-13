from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.device_metric import DeviceMetric
from app.schemas.sla import SLAResponse
from app.services.sla_service import SLAService

router = APIRouter(
    prefix="/analytics",
    tags=["SLA Analytics"],
)


def normalize_status(status: object) -> str:
    if status is None:
        return "UNKNOWN"

    value = getattr(
        status,
        "value",
        status,
    )

    normalized = str(value).upper()

    if normalized.endswith(".ONLINE"):
        return "ONLINE"

    if normalized.endswith(".OFFLINE"):
        return "OFFLINE"

    if normalized.endswith(".UNKNOWN"):
        return "UNKNOWN"

    return normalized


@router.get(
    "/sla",
    response_model=SLAResponse,
)
def get_sla_compliance(
    device_id: int | None = None,
    limit: int = Query(
        default=100,
        ge=1,
        le=10_000,
    ),
    db: Session = Depends(get_db),
):
    query = db.query(DeviceMetric)

    if device_id is not None:
        query = query.filter(
            DeviceMetric.device_id == device_id,
        )

    metrics = (
        query
        .order_by(DeviceMetric.checked_at.desc())
        .limit(limit)
        .all()
    )

    statuses = [
        normalize_status(metric.status)
        for metric in metrics
    ]

    latencies = [
        float(metric.response_time_ms)
        for metric in metrics
        if metric.response_time_ms is not None
    ]

    packet_losses = [
        float(metric.packet_loss_percent)
        for metric in metrics
        if metric.packet_loss_percent is not None
    ]

    jitters = [
        float(metric.jitter_ms)
        for metric in metrics
        if metric.jitter_ms is not None
    ]

    result = SLAService.calculate(
        statuses=statuses,
        latencies_ms=latencies,
        packet_losses_percent=packet_losses,
        jitters_ms=jitters,
    )

    return SLAResponse(
        **result.__dict__,
    )