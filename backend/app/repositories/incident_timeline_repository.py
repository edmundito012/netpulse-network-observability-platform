"""Append-only persistence operations for incident timelines."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.orm import (
    Session,
    joinedload,
)

from app.models.incident_timeline_event import (
    IncidentTimelineActorType,
    IncidentTimelineEvent,
    IncidentTimelineEventType,
)


class IncidentTimelineRepository:
    """Append and query immutable incident timeline events."""

    @staticmethod
    def append(
        db: Session,
        *,
        incident_id: int,
        event_type: IncidentTimelineEventType,
        actor_type: IncidentTimelineActorType,
        message: str,
        actor_id: int | None = None,
        actor_label: str | None = None,
        previous_value: (
            dict[str, object] | None
        ) = None,
        new_value: (
            dict[str, object] | None
        ) = None,
        event_metadata: (
            dict[str, object] | None
        ) = None,
        occurred_at: datetime | None = None,
    ) -> IncidentTimelineEvent:
        """Append one immutable event to an incident timeline."""

        event = IncidentTimelineEvent(
            incident_id=incident_id,
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id,
            actor_label=actor_label,
            message=message,
            previous_value=(
                dict(previous_value)
                if previous_value is not None
                else None
            ),
            new_value=(
                dict(new_value)
                if new_value is not None
                else None
            ),
            event_metadata=dict(
                event_metadata or {}
            ),
        )

        if occurred_at is not None:
            event.occurred_at = occurred_at

        db.add(event)
        db.commit()
        db.refresh(event)

        return event

    @staticmethod
    def get_by_id(
        db: Session,
        *,
        event_id: int,
    ) -> IncidentTimelineEvent | None:
        """Return a timeline event by its internal ID."""

        statement = (
            select(IncidentTimelineEvent)
            .where(
                IncidentTimelineEvent.id
                == event_id
            )
            .options(
                joinedload(
                    IncidentTimelineEvent.actor
                )
            )
        )

        return db.scalar(statement)

    @staticmethod
    def get_latest(
        db: Session,
        *,
        incident_id: int,
    ) -> IncidentTimelineEvent | None:
        """Return the latest event for one incident."""

        statement = (
            select(IncidentTimelineEvent)
            .where(
                IncidentTimelineEvent.incident_id
                == incident_id
            )
            .options(
                joinedload(
                    IncidentTimelineEvent.actor
                )
            )
            .order_by(
                IncidentTimelineEvent
                .occurred_at
                .desc(),
                IncidentTimelineEvent.id.desc(),
            )
            .limit(1)
        )

        return db.scalar(statement)

    @staticmethod
    def get_paginated(
        db: Session,
        *,
        incident_id: int,
        event_type: (
            IncidentTimelineEventType | None
        ) = None,
        actor_type: (
            IncidentTimelineActorType | None
        ) = None,
        page: int = 1,
        page_size: int = 50,
        newest_first: bool = False,
    ) -> dict[str, object]:
        """Return filtered timeline events with pagination metadata."""

        IncidentTimelineRepository._validate_pagination(
            page=page,
            page_size=page_size,
        )

        filters: list[object] = [
            IncidentTimelineEvent.incident_id
            == incident_id
        ]

        if event_type is not None:
            filters.append(
                IncidentTimelineEvent.event_type
                == event_type
            )

        if actor_type is not None:
            filters.append(
                IncidentTimelineEvent.actor_type
                == actor_type
            )

        count_statement = (
            select(
                func.count(
                    IncidentTimelineEvent.id
                )
            )
            .where(*filters)
        )

        total_count = int(
            db.scalar(count_statement)
            or 0
        )

        if newest_first:
            ordering = (
                IncidentTimelineEvent
                .occurred_at
                .desc(),
                IncidentTimelineEvent.id.desc(),
            )
        else:
            ordering = (
                IncidentTimelineEvent
                .occurred_at
                .asc(),
                IncidentTimelineEvent.id.asc(),
            )

        statement = (
            select(IncidentTimelineEvent)
            .where(*filters)
            .options(
                joinedload(
                    IncidentTimelineEvent.actor
                )
            )
            .order_by(*ordering)
            .offset(
                (page - 1) * page_size
            )
            .limit(page_size)
        )

        items = list(
            db.scalars(statement)
            .unique()
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
    def count_events(
        db: Session,
        *,
        incident_id: int,
    ) -> int:
        """Return the number of events recorded for an incident."""

        statement = (
            select(
                func.count(
                    IncidentTimelineEvent.id
                )
            )
            .where(
                IncidentTimelineEvent.incident_id
                == incident_id
            )
        )

        return int(
            db.scalar(statement)
            or 0
        )

    @staticmethod
    def get_first_occurred_at(
        db: Session,
        *,
        incident_id: int,
    ) -> datetime | None:
        """Return the timestamp of the first timeline event."""

        statement = (
            select(
                func.min(
                    IncidentTimelineEvent
                    .occurred_at
                )
            )
            .where(
                IncidentTimelineEvent.incident_id
                == incident_id
            )
        )

        return db.scalar(statement)

    @staticmethod
    def get_latest_occurred_at(
        db: Session,
        *,
        incident_id: int,
    ) -> datetime | None:
        """Return the timestamp of the latest timeline event."""

        statement = (
            select(
                func.max(
                    IncidentTimelineEvent
                    .occurred_at
                )
            )
            .where(
                IncidentTimelineEvent.incident_id
                == incident_id
            )
        )

        return db.scalar(statement)

    @staticmethod
    def _validate_pagination(
        *,
        page: int,
        page_size: int,
    ) -> None:
        if page < 1:
            raise ValueError(
                "page must be greater than or equal to 1"
            )

        if page_size < 1 or page_size > 200:
            raise ValueError(
                "page_size must be between 1 and 200"
            )