from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.device import Device
from app.services.failure_risk_service import (
    FailureRiskService,
)


@dataclass
class DeviceRiskResult:
    device_id: int
    device_name: str

    risk_score: int
    risk_level: str


class DeviceRiskService:

    @staticmethod
    def classify_risk_level(
        risk_score: int,
    ) -> str:

        if risk_score >= 75:
            return "HIGH"

        if risk_score >= 50:
            return "MEDIUM"

        return "LOW"

    @staticmethod
    def calculate_device_risk(
        db: Session,
        device,
    ) -> DeviceRiskResult:

        risk_data = (
            FailureRiskService.calculate(
                db=db,
                device=device,
            )
        )

        risk_score = risk_data[
            "failure_risk"
        ]

        return DeviceRiskResult(
            device_id=device.id,
            device_name=device.name,
            risk_score=risk_score,
            risk_level=(
                DeviceRiskService
                .classify_risk_level(
                    risk_score
                )
            ),
        )

    @staticmethod
    def get_risk_ranking(
        db: Session,
    ) -> list[DeviceRiskResult]:

        devices = (
            db.query(Device)
            .all()
        )

        ranking = []

        for device in devices:

            ranking.append(
                DeviceRiskService
                .calculate_device_risk(
                    db=db,
                    device=device,
                )
            )

        ranking.sort(
            key=lambda x: x.risk_score,
            reverse=True,
        )

        return ranking