"""Application service for Incident Engine operations."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.incident import (
    Incident,
    IncidentPriority,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)
from app.models.incident_alert import IncidentAlert
from app.models.incident_timeline_event import (
    IncidentTimelineActorType,
)
from app.repositories.alert_repository import (
    AlertRepository,
)
from app.repositories.incident_repository import (
    IncidentRepository,
)
from app.repositories.user_repository import (
    UserRepository,
)
from app.schemas.incident import (
    IncidentCreate,
    IncidentUpdate,
)
from app.services.incident_exceptions import (
    IncidentAlertConflictError,
    IncidentAlertNotAttachedError,
    IncidentAlertNotFoundError,
    IncidentNotFoundError,
    IncidentOwnerNotFoundError,
)
from app.services.incident_timeline_recorder_service import (
    IncidentTimelineRecorderService,
)


@dataclass(frozen=True, slots=True)
class IncidentStatistics:
    """Calculated operational statistics for one incident."""

    incident_id: int
    public_id: str

    alert_count: int
    affected_device_count: int

    duration_seconds: float
    is_active: bool


class IncidentService:
    """Coordinate incident persistence and related entities."""

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        incident_data: IncidentCreate,
    ) -> Incident:
        """Create an incident after validating all dependencies."""

        cls._validate_owner(
            db=db,
            owner_id=incident_data.owner_id,
        )

        cls._validate_alerts_for_creation(
            db=db,
            alert_ids=incident_data.alert_ids,
        )

        incident = IncidentRepository.create(
            db=db,
            title=incident_data.title,
            description=incident_data.description,
            severity=incident_data.severity,
            priority=incident_data.priority,
            source=incident_data.source,
            owner_id=incident_data.owner_id,
            business_impact=(
                incident_data.business_impact
            ),
            started_at=incident_data.started_at,
            tags=incident_data.tags,
            incident_metadata=(
                incident_data.metadata
            ),
        )

        (
            IncidentTimelineRecorderService
            .record_incident_created(
                db=db,
                incident=incident,
            )
        )

        for alert_id in incident_data.alert_ids:
            cls.attach_alert(
                db=db,
                incident=incident,
                alert_id=alert_id,
                actor_type=(
                    cls._actor_type_for_source(
                        incident.source
                    )
                ),
                actor_label=(
                    cls._actor_label_for_source(
                        incident.source
                    )
                ),
            )

        refreshed_incident = (
            IncidentRepository.get_by_id(
                db=db,
                incident_id=incident.id,
            )
        )

        return refreshed_incident or incident

    @staticmethod
    def get_required_by_id(
        db: Session,
        *,
        incident_id: int,
    ) -> Incident:
        """Return an incident or raise a domain exception."""

        incident = IncidentRepository.get_by_id(
            db=db,
            incident_id=incident_id,
        )

        if incident is None:
            raise IncidentNotFoundError(
                incident_id
            )

        return incident

    @staticmethod
    def get_required_by_public_id(
        db: Session,
        *,
        public_id: str,
    ) -> Incident:
        """Return an incident by public ID or raise."""

        incident = (
            IncidentRepository
            .get_by_public_id(
                db=db,
                public_id=public_id,
            )
        )

        if incident is None:
            raise IncidentNotFoundError(
                public_id
            )

        return incident

    @classmethod
    def update(
        cls,
        db: Session,
        *,
        incident: Incident,
        incident_data: IncidentUpdate,
        actor_type: IncidentTimelineActorType = (
            IncidentTimelineActorType.SYSTEM
        ),
        actor_id: int | None = None,
        actor_label: str | None = None,
    ) -> Incident:
        """Update editable incident information and record changes."""

        update_data = (
            incident_data.model_dump(
                exclude_unset=True
            )
        )

        if not update_data:
            return incident

        if "owner_id" in update_data:
            owner_id = update_data.pop(
                "owner_id"
            )

            cls.assign_owner(
                db=db,
                incident=incident,
                owner_id=owner_id,
                actor_type=actor_type,
                actor_id=actor_id,
                actor_label=actor_label,
            )

        metadata = update_data.pop(
            "metadata",
            None,
        )

        if not update_data and metadata is None:
            return incident

        previous_severity = (
            incident.severity
        )

        previous_priority = (
            incident.priority
        )

        previous_business_impact = (
            incident.business_impact
        )

        previous_root_cause = (
            incident.root_cause
        )

        detail_fields = {
            "title",
            "description",
            "tags",
        }

        previous_details: dict[str, Any] = {}
        new_details: dict[str, Any] = {}

        for field_name in detail_fields:
            if field_name not in update_data:
                continue

            previous_details[field_name] = getattr(
                incident,
                field_name,
            )

            new_details[field_name] = (
                update_data[field_name]
            )

        if metadata is not None:
            previous_details["metadata"] = dict(
                incident.incident_metadata or {}
            )

            new_details["metadata"] = dict(
                metadata
            )

        updated = (
            IncidentRepository.update_details(
                db=db,
                incident=incident,
                title=update_data.get("title"),
                description=update_data.get(
                    "description"
                ),
                severity=update_data.get(
                    "severity"
                ),
                priority=update_data.get(
                    "priority"
                ),
                business_impact=update_data.get(
                    "business_impact"
                ),
                root_cause=update_data.get(
                    "root_cause"
                ),
                tags=update_data.get("tags"),
                incident_metadata=metadata,
            )
        )

        if (
            "severity" in update_data
            and updated.severity
            != previous_severity
        ):
            (
                IncidentTimelineRecorderService
                .record_severity_changed(
                    db=db,
                    incident=updated,
                    previous_severity=(
                        previous_severity.value
                    ),
                    new_severity=(
                        updated.severity.value
                    ),
                    actor_type=actor_type,
                    actor_id=actor_id,
                    actor_label=actor_label,
                )
            )

        if (
            "priority" in update_data
            and updated.priority
            != previous_priority
        ):
            (
                IncidentTimelineRecorderService
                .record_priority_changed(
                    db=db,
                    incident=updated,
                    previous_priority=(
                        previous_priority.value
                    ),
                    new_priority=(
                        updated.priority.value
                    ),
                    actor_type=actor_type,
                    actor_id=actor_id,
                    actor_label=actor_label,
                )
            )

        if (
            "business_impact" in update_data
            and updated.business_impact
            != previous_business_impact
        ):
            (
                IncidentTimelineRecorderService
                .record_business_impact_updated(
                    db=db,
                    incident=updated,
                    previous_value=(
                        previous_business_impact
                    ),
                    new_value=(
                        updated.business_impact
                    ),
                    actor_type=actor_type,
                    actor_id=actor_id,
                    actor_label=actor_label,
                )
            )

        if (
            "root_cause" in update_data
            and updated.root_cause
            != previous_root_cause
        ):
            (
                IncidentTimelineRecorderService
                .record_root_cause_updated(
                    db=db,
                    incident=updated,
                    previous_value=(
                        previous_root_cause
                    ),
                    new_value=updated.root_cause,
                    actor_type=actor_type,
                    actor_id=actor_id,
                    actor_label=actor_label,
                )
            )

        changed_previous_details = {
            key: value
            for key, value
            in previous_details.items()
            if value != new_details.get(key)
        }

        changed_new_details = {
            key: new_details[key]
            for key
            in changed_previous_details
        }

        if changed_new_details:
            (
                IncidentTimelineRecorderService
                .record_details_updated(
                    db=db,
                    incident=updated,
                    previous_value=(
                        changed_previous_details
                    ),
                    new_value=(
                        changed_new_details
                    ),
                    actor_type=actor_type,
                    actor_id=actor_id,
                    actor_label=actor_label,
                )
            )

        return updated

    @classmethod
    def assign_owner(
        cls,
        db: Session,
        *,
        incident: Incident,
        owner_id: int | None,
        actor_type: IncidentTimelineActorType = (
            IncidentTimelineActorType.SYSTEM
        ),
        actor_id: int | None = None,
        actor_label: str | None = None,
    ) -> Incident:
        """Assign an existing user or remove the owner."""

        cls._validate_owner(
            db=db,
            owner_id=owner_id,
        )

        previous_owner_id = (
            incident.owner_id
        )

        if previous_owner_id == owner_id:
            return incident

        updated = IncidentRepository.assign_owner(
            db=db,
            incident=incident,
            owner_id=owner_id,
        )

        (
            IncidentTimelineRecorderService
            .record_owner_changed(
                db=db,
                incident=updated,
                previous_owner_id=(
                    previous_owner_id
                ),
                new_owner_id=owner_id,
                actor_type=actor_type,
                actor_id=actor_id,
                actor_label=actor_label,
            )
        )

        return updated

    @classmethod
    def attach_alert(
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
    ) -> IncidentAlert:
        """Attach alert evidence idempotently to an incident."""

        alert = AlertRepository.get_by_id(
            db=db,
            alert_id=alert_id,
        )

        if alert is None:
            raise IncidentAlertNotFoundError(
                alert_id
            )

        existing_link = (
            IncidentRepository.get_alert_link(
                db=db,
                alert_id=alert_id,
            )
        )

        if existing_link is not None:
            if (
                existing_link.incident_id
                == incident.id
            ):
                return existing_link

            raise IncidentAlertConflictError(
                alert_id=alert_id,
                public_id=(
                    existing_link
                    .incident
                    .public_id
                ),
            )

        try:
            link = IncidentRepository.attach_alert(
                db=db,
                incident_id=incident.id,
                alert_id=alert_id,
            )

        except IntegrityError:
            db.rollback()

            concurrent_link = (
                IncidentRepository
                .get_alert_link(
                    db=db,
                    alert_id=alert_id,
                )
            )

            if concurrent_link is None:
                raise

            if (
                concurrent_link.incident_id
                == incident.id
            ):
                return concurrent_link

            raise IncidentAlertConflictError(
                alert_id=alert_id,
                public_id=(
                    concurrent_link
                    .incident
                    .public_id
                ),
            )

        (
            IncidentTimelineRecorderService
            .record_alert_attached(
                db=db,
                incident=incident,
                alert_id=alert_id,
                actor_type=actor_type,
                actor_id=actor_id,
                actor_label=actor_label,
            )
        )

        return link

    @staticmethod
    def detach_alert(
        db: Session,
        *,
        incident: Incident,
        alert_id: int,
        actor_type: IncidentTimelineActorType = (
            IncidentTimelineActorType.SYSTEM
        ),
        actor_id: int | None = None,
        actor_label: str | None = None,
    ) -> None:
        """Detach alert evidence from an incident."""

        detached = (
            IncidentRepository.detach_alert(
                db=db,
                incident_id=incident.id,
                alert_id=alert_id,
            )
        )

        if not detached:
            raise IncidentAlertNotAttachedError(
                alert_id=alert_id,
                public_id=incident.public_id,
            )

        (
            IncidentTimelineRecorderService
            .record_alert_detached(
                db=db,
                incident=incident,
                alert_id=alert_id,
                actor_type=actor_type,
                actor_id=actor_id,
                actor_label=actor_label,
            )
        )

    @staticmethod
    def get_statistics(
        db: Session,
        *,
        incident: Incident,
        now: datetime | None = None,
    ) -> IncidentStatistics:
        """Calculate current operational incident statistics."""

        effective_now = (
            now
            or datetime.now(UTC)
        )

        end_at = (
            incident.resolved_at
            or effective_now
        )

        duration_seconds = max(
            0.0,
            (
                end_at
                - incident.started_at
            ).total_seconds(),
        )

        return IncidentStatistics(
            incident_id=incident.id,
            public_id=incident.public_id,
            alert_count=(
                IncidentRepository.count_alerts(
                    db=db,
                    incident_id=incident.id,
                )
            ),
            affected_device_count=(
                IncidentRepository
                .get_affected_device_count(
                    db=db,
                    incident_id=incident.id,
                )
            ),
            duration_seconds=round(
                duration_seconds,
                2,
            ),
            is_active=(
                incident.status
                != IncidentStatus.RESOLVED
            ),
        )

    @staticmethod
    def list_incidents(
        db: Session,
        *,
        status: IncidentStatus | None = None,
        severity: IncidentSeverity | None = None,
        priority: IncidentPriority | None = None,
        source: IncidentSource | None = None,
        owner_id: int | None = None,
        active_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, object]:
        """Return filtered incidents through the application layer."""

        return IncidentRepository.get_paginated(
            db=db,
            status=status,
            severity=severity,
            priority=priority,
            source=source,
            owner_id=owner_id,
            active_only=active_only,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def _validate_owner(
        db: Session,
        *,
        owner_id: int | None,
    ) -> None:
        if owner_id is None:
            return

        owner = UserRepository.get_by_id(
            db=db,
            user_id=owner_id,
        )

        if owner is None:
            raise IncidentOwnerNotFoundError(
                owner_id
            )

    @staticmethod
    def _validate_alerts_for_creation(
        db: Session,
        *,
        alert_ids: list[int],
    ) -> None:
        for alert_id in alert_ids:
            alert = AlertRepository.get_by_id(
                db=db,
                alert_id=alert_id,
            )

            if alert is None:
                raise IncidentAlertNotFoundError(
                    alert_id
                )

            existing_link = (
                IncidentRepository
                .get_alert_link(
                    db=db,
                    alert_id=alert_id,
                )
            )

            if existing_link is not None:
                raise IncidentAlertConflictError(
                    alert_id=alert_id,
                    public_id=(
                        existing_link
                        .incident
                        .public_id
                    ),
                )

    @staticmethod
    def _actor_type_for_source(
        source: IncidentSource,
    ) -> IncidentTimelineActorType:
        if source in {
            IncidentSource.ALERT_ENGINE,
            IncidentSource.CORRELATION_ENGINE,
            IncidentSource.ROOT_CAUSE_ENGINE,
        }:
            return (
                IncidentTimelineActorType
                .AUTOMATION
            )

        if source == IncidentSource.API:
            return IncidentTimelineActorType.API

        return IncidentTimelineActorType.SYSTEM

    @staticmethod
    def _actor_label_for_source(
        source: IncidentSource,
    ) -> str:
        if source in {
            IncidentSource.ALERT_ENGINE,
            IncidentSource.CORRELATION_ENGINE,
            IncidentSource.ROOT_CAUSE_ENGINE,
        }:
            return f"NetPulse {source.value}"

        if source == IncidentSource.API:
            return "NetPulse API"

        return "NetPulse Incident Engine"