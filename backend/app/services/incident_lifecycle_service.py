"""Incident lifecycle domain service."""

from sqlalchemy.orm import Session

from app.models.incident import (
    Incident,
    IncidentStatus,
)
from app.repositories.incident_lifecycle_repository import (
    IncidentLifecycleRepository,
)
from app.services.incident_exceptions import (
    IncidentResolutionError,
    InvalidIncidentTransitionError,
)


class IncidentLifecycleService:
    """Enforce valid incident lifecycle transitions."""

    ALLOWED_TRANSITIONS: dict[
        IncidentStatus,
        frozenset[IncidentStatus],
    ] = {
        IncidentStatus.OPEN: frozenset(
            {
                IncidentStatus.ACKNOWLEDGED,
                IncidentStatus.INVESTIGATING,
            }
        ),
        IncidentStatus.ACKNOWLEDGED: frozenset(
            {
                IncidentStatus.INVESTIGATING,
            }
        ),
        IncidentStatus.INVESTIGATING: frozenset(
            {
                IncidentStatus.MONITORING,
            }
        ),
        IncidentStatus.MONITORING: frozenset(
            {
                IncidentStatus.RESOLVED,
            }
        ),
        IncidentStatus.RESOLVED: frozenset(),
    }

    @classmethod
    def acknowledge(
        cls,
        db: Session,
        *,
        incident: Incident,
    ) -> Incident:
        """Acknowledge an open incident."""

        return cls.transition(
            db=db,
            incident=incident,
            target_status=(
                IncidentStatus.ACKNOWLEDGED
            ),
        )

    @classmethod
    def start_investigation(
        cls,
        db: Session,
        *,
        incident: Incident,
    ) -> Incident:
        """Move an incident into active investigation."""

        return cls.transition(
            db=db,
            incident=incident,
            target_status=(
                IncidentStatus.INVESTIGATING
            ),
        )

    @classmethod
    def start_monitoring(
        cls,
        db: Session,
        *,
        incident: Incident,
    ) -> Incident:
        """Mark an incident as remediated and under observation."""

        return cls.transition(
            db=db,
            incident=incident,
            target_status=IncidentStatus.MONITORING,
        )

    @classmethod
    def transition(
        cls,
        db: Session,
        *,
        incident: Incident,
        target_status: IncidentStatus,
    ) -> Incident:
        """Validate and persist a non-resolution transition."""

        if incident.status == target_status:
            return incident

        cls.validate_transition(
            current_status=incident.status,
            target_status=target_status,
        )

        if target_status == IncidentStatus.RESOLVED:
            raise IncidentResolutionError(
                "Incidents must be resolved through "
                "the dedicated resolution operation"
            )

        return (
            IncidentLifecycleRepository
            .transition(
                db=db,
                incident=incident,
                target_status=target_status,
            )
        )

    @classmethod
    def resolve(
        cls,
        db: Session,
        *,
        incident: Incident,
        resolution_summary: str,
        root_cause: str | None = None,
    ) -> Incident:
        """Resolve a monitored incident with operational context."""

        normalized_summary = (
            resolution_summary.strip()
        )

        if len(normalized_summary) < 3:
            raise IncidentResolutionError(
                "resolution_summary must contain "
                "at least 3 characters"
            )

        normalized_root_cause = (
            root_cause.strip()
            if root_cause is not None
            else None
        )

        if normalized_root_cause == "":
            normalized_root_cause = None

        cls.validate_transition(
            current_status=incident.status,
            target_status=IncidentStatus.RESOLVED,
        )

        return (
            IncidentLifecycleRepository
            .resolve(
                db=db,
                incident=incident,
                resolution_summary=(
                    normalized_summary
                ),
                root_cause=normalized_root_cause,
            )
        )

    @classmethod
    def validate_transition(
        cls,
        *,
        current_status: IncidentStatus,
        target_status: IncidentStatus,
    ) -> None:
        """Raise when a lifecycle transition is not allowed."""

        allowed_targets = (
            cls.ALLOWED_TRANSITIONS[
                current_status
            ]
        )

        if target_status not in allowed_targets:
            raise InvalidIncidentTransitionError(
                current_status=(
                    current_status.value
                ),
                target_status=(
                    target_status.value
                ),
            )