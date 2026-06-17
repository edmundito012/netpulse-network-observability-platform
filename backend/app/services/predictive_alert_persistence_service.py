from sqlalchemy.orm import Session

from app.repositories.alert_repository import AlertRepository
from app.services.predictive_alert_generation_service import (
    PredictiveAlertGenerationService,
)


class PredictiveAlertPersistenceService:

    @staticmethod
    def create_latency_alert(
        db: Session,
        device_id: int,
    ):
        active_alert = (
            AlertRepository.get_active_alert_for_device(
                db=db,
                device_id=device_id,
            )
        )

        if active_alert:
            return active_alert

        payload = (
            PredictiveAlertGenerationService
            .build_latency_alert()
        )

        return AlertRepository.create(
            db=db,
            device_id=device_id,
            severity=payload["severity"],
            message=payload["message"],
        )

    @staticmethod
    def create_packet_loss_alert(
        db: Session,
        device_id: int,
    ):
        active_alert = (
            AlertRepository.get_active_alert_for_device(
                db=db,
                device_id=device_id,
            )
        )

        if active_alert:
            return active_alert

        payload = (
            PredictiveAlertGenerationService
            .build_packet_loss_alert()
        )

        return AlertRepository.create(
            db=db,
            device_id=device_id,
            severity=payload["severity"],
            message=payload["message"],
        )

    @staticmethod
    def create_jitter_alert(
        db: Session,
        device_id: int,
    ):
        active_alert = (
            AlertRepository.get_active_alert_for_device(
                db=db,
                device_id=device_id,
            )
        )

        if active_alert:
            return active_alert

        payload = (
            PredictiveAlertGenerationService
            .build_jitter_alert()
        )

        return AlertRepository.create(
            db=db,
            device_id=device_id,
            severity=payload["severity"],
            message=payload["message"],
        )