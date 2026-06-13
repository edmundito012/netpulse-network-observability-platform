from sqlalchemy.orm import Session

from app.repositories.device_repository import DeviceRepository
from app.services.failure_risk_service import (
    FailureRiskService,
)
from app.services.health_score_service import (
    HealthScoreService,
)


class RiskService:

    @staticmethod
    def get_top_risk_devices(
        db: Session,
        limit: int = 10,
    ):
        devices = DeviceRepository.get_all(db)

        results = []

        for device in devices:

            health = HealthScoreService.calculate(
                db=db,
                device=device,
            )

            risk = FailureRiskService.calculate(
                db=db,
                device=device,
            )

            results.append(
                {
                    "device_id": device.id,
                    "device_name": device.name,
                    "health_score": health["score"],
                    "failure_risk": risk["failure_risk"],
                }
            )

        results.sort(
            key=lambda x: x["failure_risk"],
            reverse=True,
        )

        return results[:limit]