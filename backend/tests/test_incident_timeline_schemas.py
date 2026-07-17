"""Unit tests for incident timeline schemas."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.incident_timeline_event import (
    IncidentTimelineActorType,
    IncidentTimelineEventType,
)
from app.schemas.incident_timeline import (
    IncidentTimelineCommentCreate,
    IncidentTimelineEventCreate,
    IncidentTimelineEventRead,
)


NOW = datetime(
    2026,
    7,
    17,
    12,
    0,
    tzinfo=UTC,
)


def test_timeline_event_create_normalizes_text() -> None:
    payload = IncidentTimelineEventCreate(
        incident_id=7,
        event_type=(
            IncidentTimelineEventType
            .STATUS_CHANGED
        ),
        actor_type=(
            IncidentTimelineActorType.USER
        ),
        actor_id=3,
        actor_label="  NOC Operator  ",
        message=(
            "  Incident moved into investigation  "
        ),
        previous_value={
            "status": "ACKNOWLEDGED",
        },
        new_value={
            "status": "INVESTIGATING",
        },
        metadata={
            "source": "incident_lifecycle",
        },
    )

    assert payload.actor_label == "NOC Operator"

    assert payload.message == (
        "Incident moved into investigation"
    )

    assert payload.previous_value == {
        "status": "ACKNOWLEDGED",
    }

    assert payload.new_value == {
        "status": "INVESTIGATING",
    }


def test_timeline_event_defaults_to_system_actor() -> None:
    payload = IncidentTimelineEventCreate(
        incident_id=7,
        event_type=(
            IncidentTimelineEventType
            .INCIDENT_CREATED
        ),
        message="Incident created",
    )

    assert (
        payload.actor_type
        == IncidentTimelineActorType.SYSTEM
    )

    assert payload.actor_id is None
    assert payload.metadata == {}


def test_timeline_event_rejects_invalid_incident_id() -> None:
    with pytest.raises(ValidationError):
        IncidentTimelineEventCreate(
            incident_id=0,
            event_type=(
                IncidentTimelineEventType
                .INCIDENT_CREATED
            ),
            message="Incident created",
        )


def test_timeline_comment_normalizes_message() -> None:
    payload = IncidentTimelineCommentCreate(
        message=(
            "  ISP escalation opened  "
        ),
        metadata={
            "ticket": "ISP-4821",
        },
    )

    assert payload.message == (
        "ISP escalation opened"
    )

    assert payload.metadata == {
        "ticket": "ISP-4821",
    }


def test_timeline_read_maps_orm_metadata_attribute() -> None:
    class TimelineEventStub:
        id = 1
        incident_id = 7

        event_type = (
            IncidentTimelineEventType
            .AUTOMATION_ACTION
        )

        actor_type = (
            IncidentTimelineActorType
            .AUTOMATION
        )

        actor_id = None
        actor_label = "NetPulse Alert Engine"

        message = "Packet loss alert attached"

        previous_value = None

        new_value = {
            "alert_id": 42,
        }

        event_metadata = {
            "detector": "packet_loss_burst",
        }

        occurred_at = NOW

    result = (
        IncidentTimelineEventRead
        .model_validate(
            TimelineEventStub()
        )
    )

    assert result.id == 1

    assert result.metadata == {
        "detector": "packet_loss_burst",
    }

    assert (
        result.event_type
        == IncidentTimelineEventType
        .AUTOMATION_ACTION
    )