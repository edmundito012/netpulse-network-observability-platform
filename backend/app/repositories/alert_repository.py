"""Persistence operations for operational alerts."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.alert import (
    Alert,
    AlertSeverity,
    AlertStatus,
    AlertType,
)


class AlertRepository:
    """Repository responsible for alert persistence."""

    ACTIVE_STATUSES = (
        AlertStatus.OPEN,
        AlertStatus.ACKNOWLEDGED,
    )

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
            .order_by(
                Alert.created_at.desc(),
                Alert.id.desc(),
            )
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_paginated(
        db: Session,
        device_id: int | None = None,
        severity: AlertSeverity | None = None,
        status: AlertStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, object]:
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

        total_count = query.count()

        items = (
            query
            .order_by(
                Alert.created_at.desc(),
                Alert.id.desc(),
            )
            .offset(
                (page - 1) * page_size
            )
            .limit(page_size)
            .all()
        )

        total_pages = (
            (
                total_count
                + page_size
                - 1
            )
            // page_size
            if total_count > 0
            else 0
        )

        return {
            "items": items,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    @staticmethod
    def get_by_id(
        db: Session,
        alert_id: int,
    ) -> Alert | None:
        return (
            db.query(Alert)
            .filter(
                Alert.id == alert_id
            )
            .first()
        )

    @staticmethod
    def get_open_alerts(
        db: Session,
    ) -> list[Alert]:
        return (
            db.query(Alert)
            .filter(
                Alert.status == AlertStatus.OPEN
            )
            .order_by(
                Alert.created_at.desc(),
                Alert.id.desc(),
            )
            .all()
        )

    @classmethod
    def get_active_alert_for_device(
        cls,
        db: Session,
        device_id: int,
    ) -> Alert | None:
        """Legacy device-level lookup retained for compatibility."""

        return (
            db.query(Alert)
            .filter(
                Alert.device_id == device_id,
                Alert.status.in_(
                    cls.ACTIVE_STATUSES
                ),
            )
            .order_by(
                Alert.created_at.desc(),
                Alert.id.desc(),
            )
            .first()
        )

    @classmethod
    def get_active_by_deduplication_key(
        cls,
        db: Session,
        *,
        device_id: int,
        deduplication_key: str,
    ) -> Alert | None:
        """Return an active alert with the same functional identity."""

        return (
            db.query(Alert)
            .filter(
                Alert.device_id == device_id,
                Alert.deduplication_key
                == deduplication_key,
                Alert.status.in_(
                    cls.ACTIVE_STATUSES
                ),
            )
            .order_by(
                Alert.created_at.desc(),
                Alert.id.desc(),
            )
            .first()
        )

    @staticmethod
    def create(
        db: Session,
        device_id: int,
        severity: AlertSeverity,
        message: str,
        alert_type: AlertType = AlertType.GENERIC,
        deduplication_key: str | None = None,
    ) -> Alert:
        """Persist a new operational alert."""

        now = datetime.now(UTC)

        effective_key = (
            deduplication_key
            or (
                f"device:{device_id}:"
                f"{alert_type.value.lower()}"
            )
        )

        alert = Alert(
            device_id=device_id,
            alert_type=alert_type,
            deduplication_key=effective_key,
            severity=severity,
            status=AlertStatus.OPEN,
            message=message,
            occurrence_count=1,
            first_seen_at=now,
            last_seen_at=now,
        )

        db.add(alert)
        db.commit()
        db.refresh(alert)

        return alert

    @staticmethod
    def register_occurrence(
        db: Session,
        *,
        alert: Alert,
        severity: AlertSeverity,
        message: str,
    ) -> Alert:
        """Update recurrence metadata for a duplicate alert."""

        alert.occurrence_count += 1
        alert.last_seen_at = datetime.now(UTC)
        alert.message = message

        if AlertRepository.is_more_severe(
            new_severity=severity,
            current_severity=alert.severity,
        ):
            alert.severity = severity

        db.commit()
        db.refresh(alert)

        return alert

    @staticmethod
    def is_more_severe(
        *,
        new_severity: AlertSeverity,
        current_severity: AlertSeverity,
    ) -> bool:
        """Return whether a severity represents an escalation."""

        ranking = {
            AlertSeverity.INFO: 1,
            AlertSeverity.WARNING: 2,
            AlertSeverity.CRITICAL: 3,
        }

        return (
            ranking[new_severity]
            > ranking[current_severity]
        )

    @staticmethod
    def resolve(
        db: Session,
        alert: Alert,
    ) -> Alert:
        if alert.status == AlertStatus.RESOLVED:
            return alert

        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now(UTC)

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