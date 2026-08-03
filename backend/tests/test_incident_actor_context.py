"""Tests for IncidentActorContext."""

from app.models.incident_timeline_event import (
    IncidentTimelineActorType,
)
from app.services.incident_actor_context import (
    IncidentActorContext,
)


def test_user_actor_context() -> None:
    actor = IncidentActorContext.user(
        user_id=7,
        username="noc-operator",
    )

    assert (
        actor.actor_type
        == IncidentTimelineActorType.USER
    )
    assert actor.actor_id == 7
    assert actor.actor_label == "noc-operator"


def test_system_actor_context() -> None:
    actor = IncidentActorContext.system()

    assert (
        actor.actor_type
        == IncidentTimelineActorType.SYSTEM
    )
    assert actor.actor_id is None

    assert actor.actor_label == (
        "NetPulse Incident Engine"
    )


def test_automation_actor_context() -> None:
    actor = IncidentActorContext.automation(
        label="NetPulse Correlation Engine",
    )

    assert (
        actor.actor_type
        == IncidentTimelineActorType.AUTOMATION
    )
    assert actor.actor_id is None

    assert actor.actor_label == (
        "NetPulse Correlation Engine"
    )