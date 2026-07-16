"""Persistence operations for incident lifecycle transitions."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.incident import (
    Incident,
    IncidentStatus,
)


class IncidentLifecycleRepository:
    """Persist lifecycle state changes for operational incidents."""

    @staticmethod
    def transition(
        db: Session,
        *,
        incident: Incident,
        target_status: IncidentStatus,
        transitioned_at: datetime | None = None,
    ) -> Incident:
        """Persist a validated incident status transition."""

        effective_time = (
            transitioned_at
            or datetime.now(UTC)
        )

        incident.status = target_status
        incident.updated_at = effective_time

        if (
            target_status
            == IncidentStatus.ACKNOWLEDGED
            and incident.acknowledged_at is None
        ):
            incident.acknowledged_at = effective_time

        db.commit()
        db.refresh(incident)

        return incident

    @staticmethod
    def resolve(
        db: Session,
        *,
        incident: Incident,
        resolution_summary: str,
        root_cause: str | None = None,
        resolved_at: datetime | None = None,
    ) -> Incident:
        """Persist the final resolution of an incident."""

        effective_time = (
            resolved_at
            or datetime.now(UTC)
        )

        incident.status = IncidentStatus.RESOLVED
        incident.resolution_summary = resolution_summary
        incident.resolved_at = effective_time
        incident.updated_at = effective_time

        if root_cause is not None:
            incident.root_cause = root_cause

        db.commit()
        db.refresh(incident)

        return incident