from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.alert import Alert, AlertStatus
from app.schemas.network_risk import NetworkRiskResponse
from app.services.dashboard_service import DashboardService
from app.services.network_impact_service import NetworkImpactService
from app.services.network_risk_service import NetworkRiskService

router = APIRouter(
    prefix="/network",
    tags=["Network Risk"],
)


@router.get(
    "/risk",
    response_model=NetworkRiskResponse,
)
def get_network_risk(
    db: Session = Depends(get_db),
):
    dashboard = DashboardService.get_dashboard_overview(db)
    network_impact = NetworkImpactService.get_network_impact(db)

    highest_risk_device = dashboard.get("highest_risk_device")
    failure_risk = 0

    if highest_risk_device:
        failure_risk = highest_risk_device.get(
            "failure_risk",
            0,
        )

    predictive_alerts = (
        db.query(Alert)
        .filter(
            Alert.status == AlertStatus.OPEN,
            Alert.message.ilike(
                "%Predictive degradation%"
            ),
        )
        .count()
    )

    result = NetworkRiskService.calculate(
        failure_risk=failure_risk,
        network_impact=network_impact.impact_score,
        predictive_alerts=predictive_alerts,
        network_health_score=dashboard[
            "network_health_score"
        ],
    )

    return NetworkRiskResponse(
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        failure_probability=result.failure_probability,
        contributing_factors=result.contributing_factors,
    )