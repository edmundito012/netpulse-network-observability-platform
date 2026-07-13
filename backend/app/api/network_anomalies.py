"""Network anomaly analytics API."""

from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.core.analytics import MetricName
from app.db.session import get_db
from app.schemas.network_anomaly import (
    NetworkAnomalyResponse,
)
from app.services.network_anomaly_application_service import (
    NetworkAnomalyApplicationService,
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
    device_id: int | None = Query(
        default=None,
        ge=1,
        description=(
            "Device whose metric window will be analyzed. "
            "When omitted, NetPulse selects the device with "
            "the most recent metric sample."
        ),
    ),
    metric_name: MetricName = Query(
        default=MetricName.LATENCY,
    ),
    start_at: datetime | None = Query(
        default=None,
        description="Inclusive UTC start of the analysis window.",
    ),
    end_at: datetime | None = Query(
        default=None,
        description="Inclusive UTC end of the analysis window.",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=10_000,
    ),
    db: Session = Depends(get_db),
) -> NetworkAnomalyResponse:
    """Analyze a coherent historical series for one device."""

    try:
        result = (
            NetworkAnomalyApplicationService
            .analyze_device_metric(
                db=db,
                device_id=device_id,
                metric_name=metric_name,
                start_at=start_at,
                end_at=end_at,
                limit=limit,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    analysis = result.analysis

    return NetworkAnomalyResponse(
        metric_name=analysis.metric_name,
        latest_value=analysis.latest_value,
        baseline_average=analysis.baseline_average,
        baseline_std_deviation=(
            analysis.baseline_std_deviation
        ),
        z_score=analysis.z_score,
        severity=analysis.severity,
        confidence=analysis.confidence,
        anomaly_detected=analysis.anomaly_detected,
        recommendation=analysis.recommendation,
    )