from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.network_impact import (
    NetworkImpactResponse,
)
from app.services.network_impact_service import (
    NetworkImpactService,
)

router = APIRouter(
    prefix="/network",
    tags=["Network Impact"],
)


@router.get(
    "/impact",
    response_model=NetworkImpactResponse,
)
def get_network_impact(
    db: Session = Depends(get_db),
):

    result = NetworkImpactService.get_network_impact(db)

    return NetworkImpactResponse(
        impact_score=result.impact_score,
        status=result.status,
        affected_services=result.affected_services,
        message=result.message,
    )