"""Application service for immutable incident timelines."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.incident_timeline_event import (
    IncidentTimelineActorType,
    IncidentTimelineEvent,
    IncidentTimelineEventType,
)
from app.repositories.incident_timeline_repository import (
    IncidentTimelineRepository,
)
from app.repositories.user_repository import (
    UserRepository,
)
from app.schemas.incident_timeline import (
    IncidentTimelineCommentCreate,
    IncidentTimelineEventCreate,
    IncidentTimelinePaginationResponse,
    IncidentTimelineSummary,
)
from app.services.incident_service import (
    IncidentService,
)
from app.services.incident_timeline_exceptions import (
    IncidentTimelineActorError,
)


class IncidentTimelineService:
    """Append and retrieve auditable incident activity."""

    @classmethod
    def append_event(
        cls,
        db: Session,
        *,
        event_data: IncidentTimelineEventCreate,
    ) -> IncidentTimelineEvent:
        """Validate and append one timeline event."""

        IncidentService.get_required_by_id(
            db=db,
            incident_id=event_data.incident_id,
        )

        cls._validate_actor(
            db=db,
            actor_type=event_data.actor_type,
            actor_id=event_data.actor_id,
        )

        return IncidentTimelineRepository.append(
            db=db,
            incident_id=event_data.incident_id,
            event_type=event_data.event_type,
            actor_type=event_data.actor_type,
            actor_id=event_data.actor_id,
            actor_label=event_data.actor_label,
            message=event_data.message,
            previous_value=(
                event_data.previous_value
            ),
            new_value=event_data.new_value,
            event_metadata=event_data.metadata,
            occurred_at=event_data.occurred_at,
        )

    @classmethod
    def add_comment(
        cls,
        db: Session,
        *,
        incident: Incident,
        comment_data: IncidentTimelineCommentCreate,
        actor_id: int,
        actor_label: str | None = None,
    ) -> IncidentTimelineEvent:
        """Append an operator comment to an incident timeline."""

        cls._validate_actor(
            db=db,
            actor_type=(
                IncidentTimelineActorType.USER
            ),
            actor_id=actor_id,
        )

        return cls.append_event(
            db=db,
            event_data=(
                IncidentTimelineEventCreate(
                    incident_id=incident.id,
                    event_type=(
                        IncidentTimelineEventType
                        .COMMENT_ADDED
                    ),
                    actor_type=(
                        IncidentTimelineActorType
                        .USER
                    ),
                    actor_id=actor_id,
                    actor_label=actor_label,
                    message=comment_data.message,
                    metadata=comment_data.metadata,
                )
            ),
        )

    @staticmethod
    def list_events(
        db: Session,
        *,
        public_id: str,
        event_type: (
            IncidentTimelineEventType | None
        ) = None,
        actor_type: (
            IncidentTimelineActorType | None
        ) = None,
        page: int = 1,
        page_size: int = 50,
        newest_first: bool = False,
    ) -> IncidentTimelinePaginationResponse:
        """Return an incident timeline with optional filters."""

        incident = (
            IncidentService
            .get_required_by_public_id(
                db=db,
                public_id=public_id,
            )
        )

        result = (
            IncidentTimelineRepository
            .get_paginated(
                db=db,
                incident_id=incident.id,
                event_type=event_type,
                actor_type=actor_type,
                page=page,
                page_size=page_size,
                newest_first=newest_first,
            )
        )

        return (
            IncidentTimelinePaginationResponse
            .model_validate(result)
        )

    @staticmethod
    def get_latest_event(
        db: Session,
        *,
        public_id: str,
    ) -> IncidentTimelineEvent | None:
        """Return the most recent event for an incident."""

        incident = (
            IncidentService
            .get_required_by_public_id(
                db=db,
                public_id=public_id,
            )
        )

        return (
            IncidentTimelineRepository
            .get_latest(
                db=db,
                incident_id=incident.id,
            )
        )

    @staticmethod
    def get_summary(
        db: Session,
        *,
        public_id: str,
    ) -> IncidentTimelineSummary:
        """Return high-level timeline statistics."""

        incident = (
            IncidentService
            .get_required_by_public_id(
                db=db,
                public_id=public_id,
            )
        )

        latest_event = (
            IncidentTimelineRepository
            .get_latest(
                db=db,
                incident_id=incident.id,
            )
        )

        return IncidentTimelineSummary(
            incident_id=incident.id,
            public_id=incident.public_id,
            event_count=(
                IncidentTimelineRepository
                .count_events(
                    db=db,
                    incident_id=incident.id,
                )
            ),
            first_event_at=(
                IncidentTimelineRepository
                .get_first_occurred_at(
                    db=db,
                    incident_id=incident.id,
                )
            ),
            latest_event_at=(
                IncidentTimelineRepository
                .get_latest_occurred_at(
                    db=db,
                    incident_id=incident.id,
                )
            ),
            last_event_type=(
                latest_event.event_type
                if latest_event is not None
                else None
            ),
        )

    @staticmethod
    def _validate_actor(
        db: Session,
        *,
        actor_type: IncidentTimelineActorType,
        actor_id: int | None,
    ) -> None:
        """Validate actor consistency and user existence."""

        if (
            actor_type
            == IncidentTimelineActorType.USER
            and actor_id is None
        ):
            raise IncidentTimelineActorError(
                "USER timeline events require actor_id"
            )

        if actor_id is None:
            return

        actor = UserRepository.get_by_id(
            db=db,
            user_id=actor_id,
        )

        if actor is None:
            raise IncidentTimelineActorError(
                f"Timeline actor user {actor_id} "
                "was not found"
            )