"""Persistence model for immutable incident timeline events."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
    text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import Base


if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.user import User


class IncidentTimelineEventType(str, Enum):
    """Auditable event types supported by the Incident Engine."""

    INCIDENT_CREATED = "INCIDENT_CREATED"

    STATUS_CHANGED = "STATUS_CHANGED"

    ALERT_ATTACHED = "ALERT_ATTACHED"
    ALERT_DETACHED = "ALERT_DETACHED"

    OWNER_ASSIGNED = "OWNER_ASSIGNED"
    OWNER_UNASSIGNED = "OWNER_UNASSIGNED"

    SEVERITY_CHANGED = "SEVERITY_CHANGED"
    PRIORITY_CHANGED = "PRIORITY_CHANGED"

    DETAILS_UPDATED = "DETAILS_UPDATED"
    BUSINESS_IMPACT_UPDATED = "BUSINESS_IMPACT_UPDATED"
    ROOT_CAUSE_UPDATED = "ROOT_CAUSE_UPDATED"

    COMMENT_ADDED = "COMMENT_ADDED"

    INCIDENT_RESOLVED = "INCIDENT_RESOLVED"

    AUTOMATION_ACTION = "AUTOMATION_ACTION"


class IncidentTimelineActorType(str, Enum):
    """Origin responsible for producing a timeline event."""

    USER = "USER"
    SYSTEM = "SYSTEM"
    API = "API"
    AUTOMATION = "AUTOMATION"


class IncidentTimelineEvent(Base):
    """Immutable operational event belonging to one incident."""

    __tablename__ = "incident_timeline_events"

    __table_args__ = (
        Index(
            "ix_incident_timeline_events_incident_occurred",
            "incident_id",
            "occurred_at",
        ),
        Index(
            "ix_incident_timeline_events_event_type",
            "event_type",
        ),
        Index(
            "ix_incident_timeline_events_actor_id",
            "actor_id",
        ),
        Index(
            "ix_incident_timeline_events_occurred_at",
            "occurred_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    incident_id: Mapped[int] = mapped_column(
        ForeignKey(
            "incidents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    event_type: Mapped[
        IncidentTimelineEventType
    ] = mapped_column(
        SQLEnum(
            IncidentTimelineEventType,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )

    actor_type: Mapped[
        IncidentTimelineActorType
    ] = mapped_column(
        SQLEnum(
            IncidentTimelineActorType,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=IncidentTimelineActorType.SYSTEM,
        server_default=(
            IncidentTimelineActorType.SYSTEM.value
        ),
    )

    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    actor_label: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    previous_value: Mapped[
        dict[str, Any] | None
    ] = mapped_column(
        JSON,
        nullable=True,
    )

    new_value: Mapped[
        dict[str, Any] | None
    ] = mapped_column(
        JSON,
        nullable=True,
    )

    event_metadata: Mapped[
        dict[str, Any]
    ] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
        server_default=text("'{}'::json"),
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    incident: Mapped[Incident] = relationship(
        "Incident",
        lazy="joined",
    )

    actor: Mapped[User | None] = relationship(
        "User",
        lazy="joined",
    )