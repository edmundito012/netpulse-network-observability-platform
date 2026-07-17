"""Internal event recorder for Incident Engine domain operations."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.incident import (
    Incident,
    IncidentSource,
    IncidentStatus,
)
from app.models.incident_timeline_event import (
    IncidentTimelineActorType,
    IncidentTimelineEvent,
    IncidentTimelineEventType,
)
from app.repositories.incident_timeline_repository import (
    IncidentTimelineRepository,
)


class IncidentTimelineRecorderService:
    """Record validated Incident Engine operations.

    This service does not validate incidents, users or lifecycle rules.
    Those validations belong to the application services that execute
    the original operation.
    """

    DEFAULT_SYSTEM_LABEL = "NetPulse Incident Engine"

    @classmethod
    def record_incident_created(
        cls,
        db: Session,
        *,
        incident: Incident,
    ) -> IncidentTimelineEvent:
        """Record the creation of an operational incident."""

        actor_type, actor_label = (
            cls._actor_from_source(
                incident.source
            )
        )

        return cls._append(
            db=db,
            incident=incident,
            event_type=(
                IncidentTimelineEventType
                .INCIDENT_CREATED
            ),
            actor_type=actor_type,
            actor_label=actor_label,
            message=(
                f"Incident {incident.public_id} created"
            ),
            new_value={
                "public_id": incident.public_id,
                "title": incident.title,
                "status": incident.status.value,
                "severity": incident.severity.value,
                "priority": incident.priority.value,
                "source": incident.source.value,
                "owner_id": incident.owner_id,
            },
            metadata={
                "source": incident.source.value,
            },
        )

    @classmethod
    def record_status_changed(
        cls,
        db: Session,
        *,
        incident: Incident,
        previous_status: IncidentStatus,
        new_status: IncidentStatus,
        actor_type: IncidentTimelineActorType = (
            IncidentTimelineActorType.SYSTEM
        ),
        actor_id: int | None = None,
        actor_label: str | None = None,
    ) -> IncidentTimelineEvent:
        """Record a validated lifecycle transition."""

        return cls._append(
            db=db,
            incident=incident,
            event_type=(
                IncidentTimelineEventType
                .STATUS_CHANGED
            ),
            actor_type=actor_type,
            actor_id=actor_id,
            actor_label=actor_label,
            message=(
                "Incident status changed from "
                f"{previous_status.value} to "
                f"{new_status.value}"
            ),
            previous_value={
                "status": previous_status.value,
            },
            new_value={
                "status": new_status.value,
            },
        )

    @classmethod
    def record_incident_resolved(
        cls,
        db: Session,
        *,
        incident: Incident,
        previous_status: IncidentStatus,
        resolution_summary: str,
        root_cause: str | None,
        actor_type: IncidentTimelineActorType = (
            IncidentTimelineActorType.SYSTEM
        ),
        actor_id: int | None = None,
        actor_label: str | None = None,
    ) -> IncidentTimelineEvent:
        """Record final incident resolution."""

        return cls._append(
            db=db,
            incident=incident,
            event_type=(
                IncidentTimelineEventType
                .INCIDENT_RESOLVED
            ),
            actor_type=actor_type,
            actor_id=actor_id,
            actor_label=actor_label,
            message=(
                f"Incident {incident.public_id} resolved"
            ),
            previous_value={
                "status": previous_status.value,
            },
            new_value={
                "status": IncidentStatus.RESOLVED.value,
                "resolution_summary": resolution_summary,
                "root_cause": root_cause,
            },
        )

    @classmethod
    def record_alert_attached(
        cls,
        db: Session,
        *,
        incident: Incident,
        alert_id: int,
        actor_type: IncidentTimelineActorType = (
            IncidentTimelineActorType.SYSTEM
        ),
        actor_id: int | None = None,
        actor_label: str | None = None,
    ) -> IncidentTimelineEvent:
        """Record newly attached alert evidence."""

        return cls._append(
            db=db,
            incident=incident,
            event_type=(
                IncidentTimelineEventType
                .ALERT_ATTACHED
            ),
            actor_type=actor_type,
            actor_id=actor_id,
            actor_label=actor_label,
            message=(
                f"Alert {alert_id} attached to "
                f"incident {incident.public_id}"
            ),
            new_value={
                "alert_id": alert_id,
            },
        )

    @classmethod
    def record_alert_detached(
        cls,
        db: Session,
        *,
        incident: Incident,
        alert_id: int,
        actor_type: IncidentTimelineActorType = (
            IncidentTimelineActorType.SYSTEM
        ),
        actor_id: int | None = None,
        actor_label: str | None = None,
    ) -> IncidentTimelineEvent:
        """Record detached alert evidence."""

        return cls._append(
            db=db,
            incident=incident,
            event_type=(
                IncidentTimelineEventType
                .ALERT_DETACHED
            ),
            actor_type=actor_type,
            actor_id=actor_id,
            actor_label=actor_label,
            message=(
                f"Alert {alert_id} detached from "
                f"incident {incident.public_id}"
            ),
            previous_value={
                "alert_id": alert_id,
            },
        )

    @classmethod
    def record_owner_changed(
        cls,
        db: Session,
        *,
        incident: Incident,
        previous_owner_id: int | None,
        new_owner_id: int | None,
        actor_type: IncidentTimelineActorType = (
            IncidentTimelineActorType.SYSTEM
        ),
        actor_id: int | None = None,
        actor_label: str | None = None,
    ) -> IncidentTimelineEvent:
        """Record incident assignment or unassignment."""

        if new_owner_id is None:
            event_type = (
                IncidentTimelineEventType
                .OWNER_UNASSIGNED
            )

            message = (
                f"Owner removed from incident "
                f"{incident.public_id}"
            )

        else:
            event_type = (
                IncidentTimelineEventType
                .OWNER_ASSIGNED
            )

            message = (
                f"User {new_owner_id} assigned to "
                f"incident {incident.public_id}"
            )

        return cls._append(
            db=db,
            incident=incident,
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id,
            actor_label=actor_label,
            message=message,
            previous_value={
                "owner_id": previous_owner_id,
            },
            new_value={
                "owner_id": new_owner_id,
            },
        )

    @classmethod
    def record_severity_changed(
        cls,
        db: Session,
        *,
        incident: Incident,
        previous_severity: str,
        new_severity: str,
        actor_type: IncidentTimelineActorType = (
            IncidentTimelineActorType.SYSTEM
        ),
        actor_id: int | None = None,
        actor_label: str | None = None,
    ) -> IncidentTimelineEvent:
        """Record a technical severity change."""

        return cls._append(
            db=db,
            incident=incident,
            event_type=(
                IncidentTimelineEventType
                .SEVERITY_CHANGED
            ),
            actor_type=actor_type,
            actor_id=actor_id,
            actor_label=actor_label,
            message=(
                "Incident severity changed from "
                f"{previous_severity} to {new_severity}"
            ),
            previous_value={
                "severity": previous_severity,
            },
            new_value={
                "severity": new_severity,
            },
        )

    @classmethod
    def record_priority_changed(
        cls,
        db: Session,
        *,
        incident: Incident,
        previous_priority: str,
        new_priority: str,
        actor_type: IncidentTimelineActorType = (
            IncidentTimelineActorType.SYSTEM
        ),
        actor_id: int | None = None,
        actor_label: str | None = None,
    ) -> IncidentTimelineEvent:
        """Record an operational priority change."""

        return cls._append(
            db=db,
            incident=incident,
            event_type=(
                IncidentTimelineEventType
                .PRIORITY_CHANGED
            ),
            actor_type=actor_type,
            actor_id=actor_id,
            actor_label=actor_label,
            message=(
                "Incident priority changed from "
                f"{previous_priority} to {new_priority}"
            ),
            previous_value={
                "priority": previous_priority,
            },
            new_value={
                "priority": new_priority,
            },
        )

    @classmethod
    def record_business_impact_updated(
        cls,
        db: Session,
        *,
        incident: Incident,
        previous_value: str | None,
        new_value: str | None,
        actor_type: IncidentTimelineActorType = (
            IncidentTimelineActorType.SYSTEM
        ),
        actor_id: int | None = None,
        actor_label: str | None = None,
    ) -> IncidentTimelineEvent:
        """Record an update to the business impact assessment."""

        return cls._append(
            db=db,
            incident=incident,
            event_type=(
                IncidentTimelineEventType
                .BUSINESS_IMPACT_UPDATED
            ),
            actor_type=actor_type,
            actor_id=actor_id,
            actor_label=actor_label,
            message=(
                "Incident business impact updated"
            ),
            previous_value={
                "business_impact": previous_value,
            },
            new_value={
                "business_impact": new_value,
            },
        )

    @classmethod
    def record_root_cause_updated(
        cls,
        db: Session,
        *,
        incident: Incident,
        previous_value: str | None,
        new_value: str | None,
        actor_type: IncidentTimelineActorType = (
            IncidentTimelineActorType.SYSTEM
        ),
        actor_id: int | None = None,
        actor_label: str | None = None,
    ) -> IncidentTimelineEvent:
        """Record a root-cause assessment update."""

        return cls._append(
            db=db,
            incident=incident,
            event_type=(
                IncidentTimelineEventType
                .ROOT_CAUSE_UPDATED
            ),
            actor_type=actor_type,
            actor_id=actor_id,
            actor_label=actor_label,
            message="Incident root cause updated",
            previous_value={
                "root_cause": previous_value,
            },
            new_value={
                "root_cause": new_value,
            },
        )

    @classmethod
    def record_details_updated(
        cls,
        db: Session,
        *,
        incident: Incident,
        previous_value: dict[str, Any],
        new_value: dict[str, Any],
        actor_type: IncidentTimelineActorType = (
            IncidentTimelineActorType.SYSTEM
        ),
        actor_id: int | None = None,
        actor_label: str | None = None,
    ) -> IncidentTimelineEvent:
        """Record non-specialized incident field changes."""

        return cls._append(
            db=db,
            incident=incident,
            event_type=(
                IncidentTimelineEventType
                .DETAILS_UPDATED
            ),
            actor_type=actor_type,
            actor_id=actor_id,
            actor_label=actor_label,
            message="Incident details updated",
            previous_value=previous_value,
            new_value=new_value,
        )

    @classmethod
    def _append(
        cls,
        db: Session,
        *,
        incident: Incident,
        event_type: IncidentTimelineEventType,
        actor_type: IncidentTimelineActorType,
        message: str,
        actor_id: int | None = None,
        actor_label: str | None = None,
        previous_value: (
            dict[str, Any] | None
        ) = None,
        new_value: (
            dict[str, Any] | None
        ) = None,
        metadata: (
            dict[str, Any] | None
        ) = None,
    ) -> IncidentTimelineEvent:
        """Append a normalized internal timeline event."""

        return IncidentTimelineRepository.append(
            db=db,
            incident_id=incident.id,
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id,
            actor_label=(
                actor_label
                or cls.DEFAULT_SYSTEM_LABEL
            ),
            message=message,
            previous_value=previous_value,
            new_value=new_value,
            event_metadata=metadata,
        )

    @staticmethod
    def _actor_from_source(
        source: IncidentSource,
    ) -> tuple[
        IncidentTimelineActorType,
        str,
    ]:
        """Map incident creation source to a timeline actor."""

        if source in {
            IncidentSource.ALERT_ENGINE,
            IncidentSource.CORRELATION_ENGINE,
            IncidentSource.ROOT_CAUSE_ENGINE,
        }:
            return (
                IncidentTimelineActorType.AUTOMATION,
                f"NetPulse {source.value}",
            )

        if source == IncidentSource.API:
            return (
                IncidentTimelineActorType.API,
                "NetPulse API",
            )

        return (
            IncidentTimelineActorType.SYSTEM,
            IncidentTimelineRecorderService
            .DEFAULT_SYSTEM_LABEL,
        )