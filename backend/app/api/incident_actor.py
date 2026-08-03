"""Incident API actor-context helpers."""

from app.models.user import User
from app.services.incident_actor_context import (
    IncidentActorContext,
)


def build_user_actor(
    user: User,
) -> IncidentActorContext:
    """Build a timeline actor from the authenticated user."""

    return IncidentActorContext.user(
        user_id=user.id,
        username=user.username,
    )