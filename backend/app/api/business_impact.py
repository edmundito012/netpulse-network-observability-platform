from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.business_impact import (
    BusinessImpactResponse,
)

from app.services.network_impact_service import (
    NetworkImpactService,
)

from app.services.business_impact_service import (
    BusinessImpactService,
)

router = APIRouter(
    prefix="/network",
    tags=["Business Impact"],
)

@router.get(
    "/impact/business",
    response_model=BusinessImpactResponse,
)
def get_business_impact(
    db: Session = Depends(get_db),
):

    summary = (
        NetworkImpactService.get_network_summary(db)
    )

    impact = (
        NetworkImpactService.get_network_impact(db)
    )

    result = (
        BusinessImpactService.calculate_business_impact(
            impact_score=impact.impact_score,
            status=impact.status,
            latency=summary.average_latency_ms,
            packet_loss=summary.average_packet_loss_percent,
            jitter=summary.average_jitter_ms,
        )
    )

    return result