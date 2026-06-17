from fastapi import APIRouter

from app.schemas.device_risk import (
    DeviceRiskRead,
)
from app.services.device_risk_service import (
    DeviceRiskService,
)

router = APIRouter(
    prefix="/devices",
    tags=["Device Risk"],
)


@router.get(
    "/risk-ranking",
    response_model=list[DeviceRiskRead],
)
def get_device_risk_ranking():

    devices = [
        DeviceRiskService.calculate_device_risk(
            device_id=1,
            device_name="Core Router",
            health_score=40,
            failure_risk=95,
        ),
        DeviceRiskService.calculate_device_risk(
            device_id=2,
            device_name="VPN Gateway",
            health_score=65,
            failure_risk=70,
        ),
        DeviceRiskService.calculate_device_risk(
            device_id=3,
            device_name="DNS Server",
            health_score=85,
            failure_risk=30,
        ),
    ]

    devices.sort(
        key=lambda x: x.risk_score,
        reverse=True,
    )

    return devices