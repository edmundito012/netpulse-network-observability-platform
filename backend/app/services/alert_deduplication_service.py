"""Central alert creation and deduplication service."""

from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.alert import (
    Alert,
    AlertSeverity,
    AlertType,
)
from app.repositories.alert_repository import (
    AlertRepository,
)


@dataclass(frozen=True, slots=True)
class AlertDeduplicationResult:
    """Result of an alert creation or deduplication operation."""

    alert: Alert
    created: bool
    deduplicated: bool
    severity_escalated: bool


class AlertDeduplicationService:
    """Create alerts while collapsing repeated active occurrences."""

    @classmethod
    def create_or_update(
        cls,
        db: Session,
        *,
        device_id: int,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        deduplication_key: str | None = None,
    ) -> AlertDeduplicationResult:
        """Create a new alert or update its active duplicate."""

        effective_key = (
            deduplication_key
            or cls.build_deduplication_key(
                device_id=device_id,
                alert_type=alert_type,
            )
        )

        active_alert = (
            AlertRepository
            .get_active_by_deduplication_key(
                db=db,
                device_id=device_id,
                deduplication_key=effective_key,
            )
        )

        if active_alert is not None:
            return cls._register_duplicate(
                db=db,
                alert=active_alert,
                severity=severity,
                message=message,
            )

        try:
            alert = AlertRepository.create(
                db=db,
                device_id=device_id,
                alert_type=alert_type,
                deduplication_key=effective_key,
                severity=severity,
                message=message,
            )
        except IntegrityError:
            # A concurrent worker may have inserted the same active
            # alert after our initial lookup.
            db.rollback()

            concurrent_alert = (
                AlertRepository
                .get_active_by_deduplication_key(
                    db=db,
                    device_id=device_id,
                    deduplication_key=effective_key,
                )
            )

            if concurrent_alert is None:
                raise

            return cls._register_duplicate(
                db=db,
                alert=concurrent_alert,
                severity=severity,
                message=message,
            )

        return AlertDeduplicationResult(
            alert=alert,
            created=True,
            deduplicated=False,
            severity_escalated=False,
        )

    @staticmethod
    def build_deduplication_key(
        *,
        device_id: int,
        alert_type: AlertType,
    ) -> str:
        """Build a deterministic alert identity."""

        return (
            f"device:{device_id}:"
            f"{alert_type.value.lower()}"
        )

    @staticmethod
    def _register_duplicate(
        db: Session,
        *,
        alert: Alert,
        severity: AlertSeverity,
        message: str,
    ) -> AlertDeduplicationResult:
        severity_escalated = (
            AlertRepository.is_more_severe(
                new_severity=severity,
                current_severity=alert.severity,
            )
        )

        updated_alert = (
            AlertRepository.register_occurrence(
                db=db,
                alert=alert,
                severity=severity,
                message=message,
            )
        )

        return AlertDeduplicationResult(
            alert=updated_alert,
            created=False,
            deduplicated=True,
            severity_escalated=severity_escalated,
        )