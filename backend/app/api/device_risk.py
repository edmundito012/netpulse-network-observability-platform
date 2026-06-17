from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.device_risk import DeviceRiskRead
from app.services.device_risk_service import DeviceRiskService

router = APIRouter(
    prefix="/devices",
    tags=["Device Risk"],
)


@router.get(
    "/risk-ranking",
    response_model=list[DeviceRiskRead],
)
def get_device_risk_ranking(
    db: Session = Depends(get_db),
):
    return DeviceRiskService.get_risk_ranking(db)