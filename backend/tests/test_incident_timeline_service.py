"""Unit tests for IncidentTimelineService."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import (
    Mock,
    patch,
)

import pytest

from app.models.incident_timeline_event import (
    IncidentTimelineActorType,
    IncidentTimelineEventType,
)
from app.schemas.incident_timeline import (
    IncidentTimelineCommentCreate,
    IncidentTimelineEventCreate,
)
from app.services.incident_timeline_exceptions import (
    IncidentTimelineActorError,
)
from app.services.incident_timeline_service import (
    IncidentTimelineService,
)


NOW = datetime(
    2026,
    7,
    17,
    12,
    0,
    tzinfo=UTC,
)


@patch(
    "app.services.incident_timeline_service."
    "IncidentTimelineRepository.append"
)
@patch(
    "app.services.incident_timeline_service."
    "IncidentService.get_required_by_id"
)
def test_append_event_validates_incident(
    get_incident_mock: Mock,
    append_mock: Mock,
) -> None:
    db = Mock()

    get_incident_mock.return_value = (
        SimpleNamespace(
            id=7,
        )
    )

    stored_event = SimpleNamespace(
        id=1,
    )

    append_mock.return_value = stored_event

    payload = IncidentTimelineEventCreate(
        incident_id=7,
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
        occurred_at=NOW,
    )

    result = (
        IncidentTimelineService.append_event(
            db=db,
            event_data=payload,
        )
    )

    assert result is stored_event

    get_incident_mock.assert_called_once_with(
        db=db,
        incident_id=7,
    )

    append_mock.assert_called_once_with(
        db=db,
        incident_id=7,
        event_type=(
            IncidentTimelineEventType
            .INCIDENT_CREATED
        ),
        actor_type=(
            IncidentTimelineActorType
            .SYSTEM
        ),
        actor_id=None,
        actor_label="NetPulse",
        message="Incident created",
        previous_value=None,
        new_value={
            "status": "OPEN",
        },
        event_metadata={},
        occurred_at=NOW,
    )


@patch(
    "app.services.incident_timeline_service."
    "UserRepository.get_by_id"
)
def test_user_actor_must_exist(
    get_user_mock: Mock,
) -> None:
    get_user_mock.return_value = None

    with pytest.raises(
        IncidentTimelineActorError,
        match="was not found",
    ):
        (
            IncidentTimelineService
            ._validate_actor(
                db=Mock(),
                actor_type=(
                    IncidentTimelineActorType
                    .USER
                ),
                actor_id=999,
            )
        )


def test_user_actor_requires_actor_id() -> None:
    with pytest.raises(
        IncidentTimelineActorError,
        match="require actor_id",
    ):
        (
            IncidentTimelineService
            ._validate_actor(
                db=Mock(),
                actor_type=(
                    IncidentTimelineActorType
                    .USER
                ),
                actor_id=None,
            )
        )


@patch.object(
    IncidentTimelineService,
    "append_event",
)
@patch(
    "app.services.incident_timeline_service."
    "UserRepository.get_by_id"
)
def test_add_comment_creates_user_event(
    get_user_mock: Mock,
    append_event_mock: Mock,
) -> None:
    db = Mock()

    get_user_mock.return_value = (
        SimpleNamespace(
            id=3,
        )
    )

    stored_event = SimpleNamespace(
        id=12,
    )

    append_event_mock.return_value = (
        stored_event
    )

    incident = SimpleNamespace(
        id=7,
        public_id="INC-2026-000007",
    )

    comment = IncidentTimelineCommentCreate(
        message="ISP escalation opened",
        metadata={
            "ticket": "ISP-4821",
        },
    )

    result = (
        IncidentTimelineService.add_comment(
            db=db,
            incident=incident,
            comment_data=comment,
            actor_id=3,
            actor_label="NOC Operator",
        )
    )

    assert result is stored_event

    event_data = (
        append_event_mock
        .call_args
        .kwargs["event_data"]
    )

    assert event_data.incident_id == 7

    assert (
        event_data.event_type
        == IncidentTimelineEventType
        .COMMENT_ADDED
    )

    assert (
        event_data.actor_type
        == IncidentTimelineActorType.USER
    )

    assert event_data.actor_id == 3

    assert event_data.metadata == {
        "ticket": "ISP-4821",
    }


@patch(
    "app.services.incident_timeline_service."
    "IncidentTimelineRepository.get_paginated"
)
@patch(
    "app.services.incident_timeline_service."
    "IncidentService.get_required_by_public_id"
)
def test_list_events_returns_schema(
    get_incident_mock: Mock,
    get_paginated_mock: Mock,
) -> None:
    get_incident_mock.return_value = (
        SimpleNamespace(
            id=7,
            public_id="INC-2026-000007",
        )
    )

    event = SimpleNamespace(
        id=1,
        incident_id=7,
        event_type=(
            IncidentTimelineEventType
            .INCIDENT_CREATED
        ),
        actor_type=(
            IncidentTimelineActorType
            .SYSTEM
        ),
        actor_id=None,
        actor_label="NetPulse",
        message="Incident created",
        previous_value=None,
        new_value={
            "status": "OPEN",
        },
        event_metadata={},
        occurred_at=NOW,
    )

    get_paginated_mock.return_value = {
        "items": [
            event,
        ],
        "total_count": 1,
        "page": 1,
        "page_size": 50,
        "total_pages": 1,
    }

    result = (
        IncidentTimelineService.list_events(
            db=Mock(),
            public_id="INC-2026-000007",
        )
    )

    assert result.total_count == 1
    assert len(result.items) == 1

    assert (
        result.items[0].event_type
        == IncidentTimelineEventType
        .INCIDENT_CREATED
    )


@patch(
    "app.services.incident_timeline_service."
    "IncidentTimelineRepository.get_latest_occurred_at"
)
@patch(
    "app.services.incident_timeline_service."
    "IncidentTimelineRepository.get_first_occurred_at"
)
@patch(
    "app.services.incident_timeline_service."
    "IncidentTimelineRepository.count_events"
)
@patch(
    "app.services.incident_timeline_service."
    "IncidentTimelineRepository.get_latest"
)
@patch(
    "app.services.incident_timeline_service."
    "IncidentService.get_required_by_public_id"
)
def test_get_summary(
    get_incident_mock: Mock,
    get_latest_mock: Mock,
    count_mock: Mock,
    first_mock: Mock,
    latest_at_mock: Mock,
) -> None:
    get_incident_mock.return_value = (
        SimpleNamespace(
            id=7,
            public_id="INC-2026-000007",
        )
    )

    get_latest_mock.return_value = (
        SimpleNamespace(
            event_type=(
                IncidentTimelineEventType
                .STATUS_CHANGED
            )
        )
    )

    count_mock.return_value = 4
    first_mock.return_value = NOW
    latest_at_mock.return_value = NOW

    result = (
        IncidentTimelineService.get_summary(
            db=Mock(),
            public_id="INC-2026-000007",
        )
    )

    assert result.incident_id == 7
    assert result.event_count == 4

    assert (
        result.last_event_type
        == IncidentTimelineEventType
        .STATUS_CHANGED
    )