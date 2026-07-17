"""Integration tests for IncidentTimelineRepository."""

from datetime import (
    UTC,
    datetime,
    timedelta,
)

import pytest

from app.db.session import SessionLocal
from app.models.incident import (
    IncidentPriority,
    IncidentSeverity,
    IncidentSource,
)
from app.models.incident_timeline_event import (
    IncidentTimelineActorType,
    IncidentTimelineEventType,
)
from app.repositories.incident_repository import (
    IncidentRepository,
)
from app.repositories.incident_timeline_repository import (
    IncidentTimelineRepository,
)


NOW = datetime(
    2026,
    7,
    17,
    12,
    0,
    tzinfo=UTC,
)


def create_incident(
    db,
):
    """Create an incident used by timeline tests."""

    return IncidentRepository.create(
        db=db,
        title="Timeline repository incident",
        description=(
            "Incident created for timeline tests."
        ),
        severity=IncidentSeverity.CRITICAL,
        priority=IncidentPriority.HIGH,
        source=IncidentSource.API,
    )


def test_append_timeline_event() -> None:
    db = SessionLocal()

    try:
        incident = create_incident(db)

        event = (
            IncidentTimelineRepository.append(
                db=db,
                incident_id=incident.id,
                event_type=(
                    IncidentTimelineEventType
                    .INCIDENT_CREATED
                ),
                actor_type=(
                    IncidentTimelineActorType
                    .SYSTEM
                ),
                actor_label="NetPulse",
                message="Incident created",
                new_value={
                    "status": "OPEN",
                },
                event_metadata={
                    "source": "test",
                },
                occurred_at=NOW,
            )
        )

        assert event.id is not None
        assert event.incident_id == incident.id

        assert (
            event.event_type
            == IncidentTimelineEventType
            .INCIDENT_CREATED
        )

        assert event.new_value == {
            "status": "OPEN",
        }

        assert event.event_metadata == {
            "source": "test",
        }

        assert event.occurred_at == NOW
    finally:
        db.close()


def test_timeline_is_returned_chronologically() -> None:
    db = SessionLocal()

    try:
        incident = create_incident(db)

        event_times = [
            NOW,
            NOW + timedelta(minutes=2),
            NOW + timedelta(minutes=4),
        ]

        event_types = [
            (
                IncidentTimelineEventType
                .INCIDENT_CREATED
            ),
            (
                IncidentTimelineEventType
                .STATUS_CHANGED
            ),
            (
                IncidentTimelineEventType
                .COMMENT_ADDED
            ),
        ]

        for event_type, occurred_at in zip(
            event_types,
            event_times,
            strict=True,
        ):
            IncidentTimelineRepository.append(
                db=db,
                incident_id=incident.id,
                event_type=event_type,
                actor_type=(
                    IncidentTimelineActorType
                    .SYSTEM
                ),
                message=event_type.value,
                occurred_at=occurred_at,
            )

        result = (
            IncidentTimelineRepository
            .get_paginated(
                db=db,
                incident_id=incident.id,
                page=1,
                page_size=50,
            )
        )

        items = result["items"]

        assert result["total_count"] == 3

        assert [
            item.event_type
            for item in items
        ] == event_types
    finally:
        db.close()


def test_timeline_can_be_returned_newest_first() -> None:
    db = SessionLocal()

    try:
        incident = create_incident(db)

        first = (
            IncidentTimelineRepository.append(
                db=db,
                incident_id=incident.id,
                event_type=(
                    IncidentTimelineEventType
                    .INCIDENT_CREATED
                ),
                actor_type=(
                    IncidentTimelineActorType
                    .SYSTEM
                ),
                message="Incident created",
                occurred_at=NOW,
            )
        )

        latest = (
            IncidentTimelineRepository.append(
                db=db,
                incident_id=incident.id,
                event_type=(
                    IncidentTimelineEventType
                    .STATUS_CHANGED
                ),
                actor_type=(
                    IncidentTimelineActorType
                    .SYSTEM
                ),
                message="Status changed",
                occurred_at=(
                    NOW
                    + timedelta(minutes=5)
                ),
            )
        )

        result = (
            IncidentTimelineRepository
            .get_paginated(
                db=db,
                incident_id=incident.id,
                newest_first=True,
            )
        )

        items = result["items"]

        assert items[0].id == latest.id
        assert items[1].id == first.id
    finally:
        db.close()


def test_timeline_filters_by_event_type() -> None:
    db = SessionLocal()

    try:
        incident = create_incident(db)

        IncidentTimelineRepository.append(
            db=db,
            incident_id=incident.id,
            event_type=(
                IncidentTimelineEventType
                .INCIDENT_CREATED
            ),
            actor_type=(
                IncidentTimelineActorType
                .SYSTEM
            ),
            message="Incident created",
        )

        IncidentTimelineRepository.append(
            db=db,
            incident_id=incident.id,
            event_type=(
                IncidentTimelineEventType
                .COMMENT_ADDED
            ),
            actor_type=(
                IncidentTimelineActorType
                .USER
            ),
            actor_label="NOC Operator",
            message="Investigation started",
        )

        result = (
            IncidentTimelineRepository
            .get_paginated(
                db=db,
                incident_id=incident.id,
                event_type=(
                    IncidentTimelineEventType
                    .COMMENT_ADDED
                ),
            )
        )

        assert result["total_count"] == 1

        assert (
            result["items"][0].event_type
            == IncidentTimelineEventType
            .COMMENT_ADDED
        )
    finally:
        db.close()


def test_get_latest_and_timeline_statistics() -> None:
    db = SessionLocal()

    try:
        incident = create_incident(db)

        IncidentTimelineRepository.append(
            db=db,
            incident_id=incident.id,
            event_type=(
                IncidentTimelineEventType
                .INCIDENT_CREATED
            ),
            actor_type=(
                IncidentTimelineActorType
                .SYSTEM
            ),
            message="Incident created",
            occurred_at=NOW,
        )

        latest = (
            IncidentTimelineRepository.append(
                db=db,
                incident_id=incident.id,
                event_type=(
                    IncidentTimelineEventType
                    .STATUS_CHANGED
                ),
                actor_type=(
                    IncidentTimelineActorType
                    .SYSTEM
                ),
                message="Investigation started",
                occurred_at=(
                    NOW
                    + timedelta(minutes=10)
                ),
            )
        )

        stored_latest = (
            IncidentTimelineRepository
            .get_latest(
                db=db,
                incident_id=incident.id,
            )
        )

        assert stored_latest is not None
        assert stored_latest.id == latest.id

        assert (
            IncidentTimelineRepository
            .count_events(
                db=db,
                incident_id=incident.id,
            )
            == 2
        )

        assert (
            IncidentTimelineRepository
            .get_first_occurred_at(
                db=db,
                incident_id=incident.id,
            )
            == NOW
        )

        assert (
            IncidentTimelineRepository
            .get_latest_occurred_at(
                db=db,
                incident_id=incident.id,
            )
            == (
                NOW
                + timedelta(minutes=10)
            )
        )
    finally:
        db.close()


@pytest.mark.parametrize(
    ("page", "page_size"),
    [
        (0, 50),
        (1, 0),
        (1, 201),
    ],
)
def test_invalid_timeline_pagination_is_rejected(
    page: int,
    page_size: int,
) -> None:
    db = SessionLocal()

    try:
        with pytest.raises(ValueError):
            (
                IncidentTimelineRepository
                .get_paginated(
                    db=db,
                    incident_id=1,
                    page=page,
                    page_size=page_size,
                )
            )
    finally:
        db.close()


def test_repository_exposes_no_mutation_operations() -> None:
    """Timeline repository intentionally exposes append-only writes."""

    assert not hasattr(
        IncidentTimelineRepository,
        "update",
    )

    assert not hasattr(
        IncidentTimelineRepository,
        "delete",
    )