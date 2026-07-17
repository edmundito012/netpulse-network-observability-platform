"""Incident lifecycle domain service."""

from sqlalchemy.orm import Session

from app.models.incident import (
    Incident,
    IncidentStatus,
)
from app.models.incident_timeline_event import (
    IncidentTimelineActorType,
)
from app.repositories.incident_lifecycle_repository import (
    IncidentLifecycleRepository,
)
from app.services.incident_exceptions import (
    IncidentResolutionError,
    InvalidIncidentTransitionError,
)
from app.services.incident_timeline_recorder_service import (
    IncidentTimelineRecorderService,
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
        actor_type: IncidentTimelineActorType = (
            IncidentTimelineActorType.SYSTEM
        ),
        actor_id: int | None = None,
        actor_label: str | None = None,
    ) -> Incident:
        """Acknowledge an open incident."""

        return cls.transition(
            db=db,
            incident=incident,
            target_status=(
                IncidentStatus.ACKNOWLEDGED
            ),
            actor_type=actor_type,
            actor_id=actor_id,
            actor_label=actor_label,
        )

    @classmethod
    def start_investigation(
        cls,
        db: Session,
        *,
        incident: Incident,
        actor_type: IncidentTimelineActorType = (
            IncidentTimelineActorType.SYSTEM
        ),
        actor_id: int | None = None,
        actor_label: str | None = None,
    ) -> Incident:
        """Move an incident into active investigation."""

        return cls.transition(
            db=db,
            incident=incident,
            target_status=(
                IncidentStatus.INVESTIGATING
            ),
            actor_type=actor_type,
            actor_id=actor_id,
            actor_label=actor_label,
        )

    @classmethod
    def start_monitoring(
        cls,
        db: Session,
        *,
        incident: Incident,
        actor_type: IncidentTimelineActorType = (
            IncidentTimelineActorType.SYSTEM
        ),
        actor_id: int | None = None,
        actor_label: str | None = None,
    ) -> Incident:
        """Mark an incident as remediated and under observation."""

        return cls.transition(
            db=db,
            incident=incident,
            target_status=IncidentStatus.MONITORING,
            actor_type=actor_type,
            actor_id=actor_id,
            actor_label=actor_label,
        )

    @classmethod
    def transition(
        cls,
        db: Session,
        *,
        incident: Incident,
        target_status: IncidentStatus,
        actor_type: IncidentTimelineActorType = (
            IncidentTimelineActorType.SYSTEM
        ),
        actor_id: int | None = None,
        actor_label: str | None = None,
    ) -> Incident:
        """Validate, persist and record a lifecycle transition."""

        if incident.status == target_status:
            return incident

        previous_status = incident.status

        cls.validate_transition(
            current_status=previous_status,
            target_status=target_status,
        )

        if target_status == IncidentStatus.RESOLVED:
            raise IncidentResolutionError(
                "Incidents must be resolved through "
                "the dedicated resolution operation"
            )

        updated = (
            IncidentLifecycleRepository
            .transition(
                db=db,
                incident=incident,
                target_status=target_status,
            )
        )

        (
            IncidentTimelineRecorderService
            .record_status_changed(
                db=db,
                incident=updated,
                previous_status=previous_status,
                new_status=target_status,
                actor_type=actor_type,
                actor_id=actor_id,
                actor_label=actor_label,
            )
        )

        return updated

    @classmethod
    def resolve(
        cls,
        db: Session,
        *,
        incident: Incident,
        resolution_summary: str,
        root_cause: str | None = None,
        actor_type: IncidentTimelineActorType = (
            IncidentTimelineActorType.SYSTEM
        ),
        actor_id: int | None = None,
        actor_label: str | None = None,
    ) -> Incident:
        """Resolve and record a monitored incident."""

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

        previous_status = incident.status

        cls.validate_transition(
            current_status=previous_status,
            target_status=IncidentStatus.RESOLVED,
        )

        updated = (
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

        (
            IncidentTimelineRecorderService
            .record_incident_resolved(
                db=db,
                incident=updated,
                previous_status=previous_status,
                resolution_summary=(
                    normalized_summary
                ),
                root_cause=(
                    normalized_root_cause
                ),
                actor_type=actor_type,
                actor_id=actor_id,
                actor_label=actor_label,
            )
        )

        return updated

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