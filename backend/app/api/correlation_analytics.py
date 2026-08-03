"""Correlation Engine analytics API."""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.user import (
    User,
    UserRole,
)
from app.schemas.correlation_analytics import (
    CorrelationAnalyticsSummary,
)
from app.services.correlation_analytics_service import (
    CorrelationAnalyticsService,
)


router = APIRouter(
    prefix="/analytics/correlations",
    tags=["Correlation Analytics"],
)


read_access = require_roles(
    UserRole.ADMIN,
    UserRole.OPERATOR,
    UserRole.VIEWER,
)


@router.get(
    "",
    response_model=CorrelationAnalyticsSummary,
    summary="Get Correlation Engine analytics",
)
def get_correlation_analytics(
    window_hours: int = Query(
        default=24,
        ge=1,
        le=720,
    ),
    recent_limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        read_access
    ),
) -> CorrelationAnalyticsSummary:
    """Return operational Correlation Engine analytics."""

    del current_user

    try:
        return (
            CorrelationAnalyticsService
            .get_summary(
                db=db,
                window_hours=window_hours,
                recent_limit=recent_limit,
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status
                .HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail=str(exc),
        ) from exc