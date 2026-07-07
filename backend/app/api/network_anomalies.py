from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.device_metric import DeviceMetric
from app.schemas.network_anomaly import NetworkAnomalyResponse
from app.services.network_anomaly_service import (
    NetworkAnomalyService,
)

router = APIRouter(
    prefix="/analytics",
    tags=["Network Analytics"],
)


@router.get(
    "/network-anomalies",
    response_model=NetworkAnomalyResponse,
)
def get_network_anomalies(
    device_id: int | None = None,
    metric_name: str = "latency",
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

    metrics = list(
        reversed(metrics)
    )

    if metric_name == "jitter":
        values = [
            metric.jitter_ms or 0
            for metric in metrics
        ]

    elif metric_name == "packet_loss":
        values = [
            metric.packet_loss_percent or 0
            for metric in metrics
        ]

    else:
        values = [
            metric.response_time_ms or 0
            for metric in metrics
        ]

        metric_name = "latency"

    result = NetworkAnomalyService.analyze(
        values=values,
        metric_name=metric_name,
    )

    return NetworkAnomalyResponse(
        **result.__dict__,
    )