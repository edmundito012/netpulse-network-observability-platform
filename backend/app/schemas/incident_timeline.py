"""Pydantic schemas for incident timeline operations."""

from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.models.incident_timeline_event import (
    IncidentTimelineActorType,
    IncidentTimelineEventType,
)


class IncidentTimelineEventCreate(BaseModel):
    """Internal command used to append a timeline event."""

    incident_id: int = Field(
        ge=1,
    )

    event_type: IncidentTimelineEventType

    actor_type: IncidentTimelineActorType = (
        IncidentTimelineActorType.SYSTEM
    )

    actor_id: int | None = Field(
        default=None,
        ge=1,
    )

    actor_label: str | None = Field(
        default=None,
        max_length=255,
    )

    message: str = Field(
        min_length=3,
        max_length=10_000,
    )

    previous_value: dict[str, Any] | None = None
    new_value: dict[str, Any] | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    occurred_at: datetime | None = None

    @field_validator(
        "message",
        "actor_label",
    )
    @classmethod
    def normalize_text(
        cls,
        value: str | None,
    ) -> str | None:
        """Strip surrounding whitespace from textual values."""

        if value is None:
            return None

        normalized = value.strip()

        return normalized or None


class IncidentTimelineCommentCreate(BaseModel):
    """Operator comment to append to an incident timeline."""

    message: str = Field(
        min_length=3,
        max_length=10_000,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    @field_validator("message")
    @classmethod
    def normalize_message(
        cls,
        value: str,
    ) -> str:
        """Normalize operator comments."""

        return value.strip()


class IncidentTimelineEventRead(BaseModel):
    """One immutable incident timeline event."""

    id: int
    incident_id: int

    event_type: IncidentTimelineEventType
    actor_type: IncidentTimelineActorType

    actor_id: int | None
    actor_label: str | None

    message: str

    previous_value: dict[str, Any] | None
    new_value: dict[str, Any] | None

    metadata: dict[str, Any] = Field(
        validation_alias="event_metadata",
    )

    occurred_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class IncidentTimelinePaginationResponse(BaseModel):
    """Paginated chronological incident timeline."""

    items: list[IncidentTimelineEventRead]

    total_count: int = Field(
        ge=0,
    )

    page: int = Field(
        ge=1,
    )

    page_size: int = Field(
        ge=1,
    )

    total_pages: int = Field(
        ge=0,
    )


class IncidentTimelineSummary(BaseModel):
    """High-level timeline statistics for one incident."""

    incident_id: int
    public_id: str

    event_count: int = Field(
        ge=0,
    )

    first_event_at: datetime | None
    latest_event_at: datetime | None

    last_event_type: (
        IncidentTimelineEventType | None
    )