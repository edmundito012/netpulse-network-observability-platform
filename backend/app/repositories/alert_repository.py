from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.alert import Alert, AlertSeverity, AlertStatus


class AlertRepository:

    @staticmethod
    def get_all(
        db: Session,
        device_id: int | None = None,
        severity: AlertSeverity | None = None,
        status: AlertStatus | None = None,
        limit: int = 100,
    ) -> list[Alert]:

        query = db.query(Alert)

        if device_id is not None:
            query = query.filter(
                Alert.device_id == device_id
            )

        if severity is not None:
            query = query.filter(
                Alert.severity == severity
            )

        if status is not None:
            query = query.filter(
                Alert.status == status
            )

        return (
            query
            .order_by(Alert.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        alert_id: int,
    ) -> Alert | None:

        return (
            db.query(Alert)
            .filter(Alert.id == alert_id)
            .first()
        )

    @staticmethod
    def get_open_alerts(
        db: Session,
    ) -> list[Alert]:

        return (
            db.query(Alert)
            .filter(Alert.status == AlertStatus.OPEN)
            .order_by(Alert.created_at.desc())
            .all()
        )

    @staticmethod
    def get_active_alert_for_device(
        db: Session,
        device_id: int,
    ) -> Alert | None:

        return (
            db.query(Alert)
            .filter(
                Alert.device_id == device_id,
                Alert.status.in_(
                    [
                        AlertStatus.OPEN,
                        AlertStatus.ACKNOWLEDGED,
                    ]
                ),
            )
            .first()
        )

    @staticmethod
    def create(
        db: Session,
        device_id: int,
        severity: AlertSeverity,
        message: str,
    ) -> Alert:

        alert = Alert(
            device_id=device_id,
            severity=severity,
            status=AlertStatus.OPEN,
            message=message,
        )

        db.add(alert)
        db.commit()
        db.refresh(alert)

        return alert

    @staticmethod
    def resolve(
        db: Session,
        alert: Alert,
    ) -> Alert:

        if alert.status == AlertStatus.RESOLVED:
            return alert

        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(alert)

        return alert

    @staticmethod
    def acknowledge(
        db: Session,
        alert: Alert,
    ) -> Alert:

        if alert.status == AlertStatus.ACKNOWLEDGED:
            return alert

        alert.status = AlertStatus.ACKNOWLEDGED

        db.commit()
        db.refresh(alert)

        return alert