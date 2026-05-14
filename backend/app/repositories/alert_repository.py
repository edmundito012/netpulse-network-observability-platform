from sqlalchemy.orm import Session

from app.models.alert import Alert, AlertStatus
from datetime import datetime, timezone

class AlertRepository:

    @staticmethod
    def get_open_alert_for_device(
        db: Session,
        device_id: int,
    ):
        return (
            db.query(Alert)
            .filter(
                Alert.device_id == device_id,
                Alert.status == AlertStatus.OPEN,
            )
            .first()
        )

    @staticmethod
    def create(
        db: Session,
        device_id: int,
        severity,
        message: str,
    ):
        alert = Alert(
            device_id=device_id,
            severity=severity,
            message=message,
            status=AlertStatus.OPEN,
        )

        db.add(alert)
        db.commit()
        db.refresh(alert)

        return alert

    @staticmethod
    def resolve(
        db: Session,
        alert: Alert,
    ):
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(alert)

        return alert