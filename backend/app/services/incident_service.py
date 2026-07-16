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

        for alert_id in incident_data.alert_ids:
            cls.attach_alert(
                db=db,
                incident=incident,
                alert_id=alert_id,
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
    ) -> Incident:
        """Update editable incident information."""

        update_data = (
            incident_data.model_dump(
                exclude_unset=True
            )
        )

        if "owner_id" in update_data:
            owner_id = update_data.pop(
                "owner_id"
            )

            cls.assign_owner(
                db=db,
                incident=incident,
                owner_id=owner_id,
            )

        metadata = update_data.pop(
            "metadata",
            None,
        )

        if not update_data and metadata is None:
            return incident

        return IncidentRepository.update_details(
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

    @classmethod
    def assign_owner(
        cls,
        db: Session,
        *,
        incident: Incident,
        owner_id: int | None,
    ) -> Incident:
        """Assign an existing user or remove the owner."""

        cls._validate_owner(
            db=db,
            owner_id=owner_id,
        )

        return IncidentRepository.assign_owner(
            db=db,
            incident=incident,
            owner_id=owner_id,
        )

    @classmethod
    def attach_alert(
        cls,
        db: Session,
        *,
        incident: Incident,
        alert_id: int,
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
            return IncidentRepository.attach_alert(
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

    @staticmethod
    def detach_alert(
        db: Session,
        *,
        incident: Incident,
        alert_id: int,
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

    @staticmethod
    def get_statistics(
        db: Session,
        *,
        incident: Incident,
        now: datetime | None = None,
    ) -> IncidentStatistics:
        """Calculate current operational incident statistics."""

        effective_now = now or datetime.now(UTC)

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