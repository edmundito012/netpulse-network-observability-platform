from sqlalchemy.orm import Session

from app.repositories.alert_repository import AlertRepository
from app.repositories.device_metric_repository import (
    DeviceMetricRepository,
)
from app.services.health_score_service import (
    HealthScoreService,
)
from app.services.recommendation_service import RecommendationService

class FailureRiskService:

    @staticmethod
    def calculate(
        db: Session,
        device,
    ):
        health = HealthScoreService.calculate(
            db=db,
            device=device,
        )

        health_score = health["score"]

        risk = 100 - health_score

        metrics = (
            DeviceMetricRepository.get_latest_metrics(
                db=db,
                device_id=device.id,
                limit=1,
            )
        )

        if metrics:

            metric = metrics[0]

            packet_loss = metric.packet_loss_percent or 0

            if packet_loss > 20:
                risk += 25

            elif packet_loss > 5:
                risk += 10

        active_alert = (
            AlertRepository.get_active_alert_for_device(
                db=db,
                device_id=device.id,
            )
        )

        if active_alert:
            risk += 15

        risk = min(risk, 100)

        if risk < 20:
            recommendation = RecommendationService.generate(
                db=db,
                device=device,
            )

        elif risk < 50:
            recommendation = RecommendationService.generate(
                db=db,
                device=device,
            )

        elif risk < 80:
            recommendation = RecommendationService.generate(
                db=db,
                device=device,
            )

        else:
            recommendation = RecommendationService.generate(
                db=db,
                device=device,
            )

        return {
            "device_id": device.id,
            "device_name": device.name,
            "health_score": health_score,
            "failure_risk": risk,
            "recommendation": recommendation,
        }