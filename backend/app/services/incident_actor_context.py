"""Actor context propagated through Incident Engine commands."""

from dataclasses import dataclass

from app.models.incident_timeline_event import (
    IncidentTimelineActorType,
)


@dataclass(frozen=True, slots=True)
class IncidentActorContext:
    """Identity responsible for an Incident Engine operation."""

    actor_type: IncidentTimelineActorType
    actor_id: int | None = None
    actor_label: str | None = None

    @classmethod
    def system(
        cls,
        *,
        label: str = "NetPulse Incident Engine",
    ) -> "IncidentActorContext":
        """Build a system actor context."""

        return cls(
            actor_type=(
                IncidentTimelineActorType.SYSTEM
            ),
            actor_label=label,
        )

    @classmethod
    def user(
        cls,
        *,
        user_id: int,
        username: str,
    ) -> "IncidentActorContext":
        """Build an authenticated user actor context."""

        return cls(
            actor_type=(
                IncidentTimelineActorType.USER
            ),
            actor_id=user_id,
            actor_label=username,
        )

    @classmethod
    def automation(
        cls,
        *,
        label: str,
    ) -> "IncidentActorContext":
        """Build an automated engine actor context."""

        return cls(
            actor_type=(
                IncidentTimelineActorType.AUTOMATION
            ),
            actor_label=label,
        )