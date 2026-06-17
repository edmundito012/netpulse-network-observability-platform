from dataclasses import dataclass


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
        device_id: int,
        device_name: str,
        health_score: int,
        failure_risk: int,
    ) -> DeviceRiskResult:

        health_risk = (
            100 - health_score
        )

        risk_score = int(
            failure_risk * 0.70
            + health_risk * 0.30
        )

        return DeviceRiskResult(
            device_id=device_id,
            device_name=device_name,
            risk_score=risk_score,
            risk_level=(
                DeviceRiskService
                .classify_risk_level(
                    risk_score
                )
            ),
        )