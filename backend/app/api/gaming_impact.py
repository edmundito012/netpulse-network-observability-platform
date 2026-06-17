from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.gaming_impact import GamingImpactResponse
from app.services.gaming_impact_service import GamingImpactService
from app.services.network_impact_service import NetworkImpactService

router = APIRouter(
    prefix="/network",
    tags=["Gaming Impact"],
)


@router.get(
    "/impact/gaming",
    response_model=GamingImpactResponse,
)
def get_gaming_impact(
    db: Session = Depends(get_db),
):
    summary = NetworkImpactService.get_network_summary(db)
    impact = NetworkImpactService.get_network_impact(db)

    result = GamingImpactService.calculate_gaming_impact(
        impact_score=impact.impact_score,
        status=impact.status,
        latency=summary.average_latency_ms,
        packet_loss=summary.average_packet_loss_percent,
        jitter=summary.average_jitter_ms,
    )

    return GamingImpactResponse(
        impact_score=result.impact_score,
        status=result.status,
        gaming_quality=result.gaming_quality,
        lag_risk=result.lag_risk,
        packet_loss_risk=result.packet_loss_risk,
        jitter_risk=result.jitter_risk,
        recommended_action=result.recommended_action,
    )