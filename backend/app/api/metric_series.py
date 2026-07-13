"""Temporal metric series API."""

from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.core.analytics import (
    MetricName,
    MissingValuePolicy,
    SortDirection,
)
from app.db.session import get_db
from app.schemas.metric_series import (
    MetricSeriesResponse,
    MetricSeriesSample,
)
from app.services.metric_series_service import (
    MetricSeriesService,
)


router = APIRouter(
    prefix="/analytics",
    tags=["Network Analytics"],
)


@router.get(
    "/metric-series",
    response_model=MetricSeriesResponse,
    summary="Retrieve a temporal device metric window",
)
def get_metric_series(
    device_id: int = Query(
        ge=1,
        description="Device whose metric history will be queried.",
    ),
    metric_name: MetricName = Query(
        default=MetricName.LATENCY,
    ),
    start_at: datetime | None = Query(
        default=None,
        description="Inclusive UTC start of the metric window.",
    ),
    end_at: datetime | None = Query(
        default=None,
        description="Inclusive UTC end of the metric window.",
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=10_000,
    ),
    sort_direction: SortDirection = Query(
        default=SortDirection.ASCENDING,
    ),
    missing_value_policy: MissingValuePolicy = Query(
        default=MissingValuePolicy.DROP,
    ),
    db: Session = Depends(get_db),
) -> MetricSeriesResponse:
    """Return a deterministic historical metric series."""

    try:
        result = MetricSeriesService.get_series(
            db=db,
            device_id=device_id,
            metric_name=metric_name,
            start_at=start_at,
            end_at=end_at,
            limit=limit,
            sort_direction=sort_direction,
            missing_value_policy=missing_value_policy,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return MetricSeriesResponse(
        device_id=result.device_id,
        metric_name=result.metric_name,
        start_at=result.start_at,
        end_at=result.end_at,
        requested_limit=result.requested_limit,
        sort_direction=result.sort_direction,
        missing_value_policy=result.missing_value_policy,
        database_sample_count=result.database_sample_count,
        returned_sample_count=result.returned_sample_count,
        missing_sample_count=result.missing_sample_count,
        samples=[
            MetricSeriesSample(
                metric_id=sample.metric_id,
                device_id=sample.device_id,
                checked_at=sample.checked_at,
                value=sample.value,
            )
            for sample in result.samples
        ],
    )