"""SLA analytics API."""

from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.sla import SLAResponse
from app.services.sla_application_service import (
    SLAApplicationService,
)


router = APIRouter(
    prefix="/analytics",
    tags=["SLA Analytics"],
)


@router.get(
    "/sla",
    response_model=SLAResponse,
)
def get_sla_compliance(
    device_id: int | None = Query(
        default=None,
        ge=1,
        description=(
            "Device whose SLA window will be calculated. "
            "When omitted, NetPulse selects the device with "
            "the most recent metric sample."
        ),
    ),
    start_at: datetime | None = Query(
        default=None,
        description="Inclusive UTC start of the SLA window.",
    ),
    end_at: datetime | None = Query(
        default=None,
        description="Inclusive UTC end of the SLA window.",
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=10_000,
    ),
    db: Session = Depends(get_db),
) -> SLAResponse:
    """Calculate SLA compliance for one coherent device series."""

    try:
        result = SLAApplicationService.calculate_compliance(
            db=db,
            device_id=device_id,
            start_at=start_at,
            end_at=end_at,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return SLAResponse(
        **result.__dict__,
    )