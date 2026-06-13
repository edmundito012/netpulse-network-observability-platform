from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.models.device import Device, DeviceStatus
from app.repositories.device_event_repository import DeviceEventRepository
from app.core.dashboard_cache import update_dashboard_state
from app.services.health_score_service import HealthScoreService
from app.services.failure_risk_service import FailureRiskService

class DashboardService:

    @staticmethod
    def get_dashboard_overview(db: Session):
        total_devices = db.query(Device).count()

        online_devices = (
            db.query(Device)
            .filter(Device.status == DeviceStatus.ONLINE)
            .count()
        )

        offline_devices = (
            db.query(Device)
            .filter(Device.status == DeviceStatus.OFFLINE)
            .count()
        )

        unknown_devices = (
            db.query(Device)
            .filter(Device.status == DeviceStatus.UNKNOWN)
            .count()
        )

        open_alerts = (
            db.query(Alert)
            .filter(Alert.status == AlertStatus.OPEN)
            .count()
        )

        acknowledged_alerts = (
            db.query(Alert)
            .filter(Alert.status == AlertStatus.ACKNOWLEDGED)
            .count()
        )

        resolved_alerts = (
            db.query(Alert)
            .filter(Alert.status == AlertStatus.RESOLVED)
            .count()
        )

        critical_alerts = (
            db.query(Alert)
            .filter(Alert.severity == AlertSeverity.CRITICAL)
            .count()
        )

        warning_alerts = (
            db.query(Alert)
            .filter(Alert.severity == AlertSeverity.WARNING)
            .count()
        )

        info_alerts = (
            db.query(Alert)
            .filter(Alert.severity == AlertSeverity.INFO)
            .count()
        )

        latest_events = DeviceEventRepository.get_all(
            db=db,
            limit=10,
        )

        devices = db.query(Device).all()

        health_scores = []

        for device in devices:
            result = HealthScoreService.calculate(
                db=db,
                device=device,
            )

            health_scores.append(result["score"])

        network_health_score = 100

        if health_scores:
            network_health_score = int(
                sum(health_scores) / len(health_scores)
            )
        devices_at_risk = 0
        highest_risk_device = None
        highest_risk = -1

        for device in devices:

            risk_data = FailureRiskService.calculate(
                db=db,
                device=device,
            )

            risk = risk_data["failure_risk"]

            if risk >= 50:
                devices_at_risk += 1

            if risk > highest_risk:
                highest_risk = risk

                highest_risk_device = {
                    "device_id": device.id,
                    "device_name": device.name,
                    "health_score": risk_data["health_score"],
                    "failure_risk": risk,
                }

        return {
            "total_devices": total_devices,
            "online_devices": online_devices,
            "offline_devices": offline_devices,
            "unknown_devices": unknown_devices,
            "network_health_score": network_health_score,
            "open_alerts": open_alerts,
            "acknowledged_alerts": acknowledged_alerts,
            "resolved_alerts": resolved_alerts,
            "critical_alerts": critical_alerts,
            "warning_alerts": warning_alerts,
            "info_alerts": info_alerts,
            "devices_at_risk": devices_at_risk,
            "highest_risk_device": highest_risk_device,
            "latest_events": latest_events,
        }

    @staticmethod
    def refresh_dashboard_cache(db: Session):
        overview = DashboardService.get_dashboard_overview(db)

        encoded_overview = jsonable_encoder(overview)

        update_dashboard_state(encoded_overview)

        return encoded_overview