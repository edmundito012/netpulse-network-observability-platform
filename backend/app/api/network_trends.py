from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.device_metric import DeviceMetric
from app.schemas.network_trend import NetworkTrendResponse
from app.services.network_trend_service import NetworkTrendService

router = APIRouter(
    prefix="/analytics",
    tags=["Network Analytics"],
)


@router.get(
    "/network-trends",
    response_model=NetworkTrendResponse,
)
def get_network_trends(
    device_id: int | None = None,
    limit: int = 20,
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

    latencies = [
        metric.response_time_ms or 0
        for metric in reversed(metrics)
    ]

    result = NetworkTrendService.analyze(
        latencies,
    )

    return NetworkTrendResponse(
        **result.__dict__,
    )