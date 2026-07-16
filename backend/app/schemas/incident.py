"""Pydantic schemas for the Incident Engine."""

from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.models.alert import (
    AlertSeverity,
    AlertStatus,
    AlertType,
)
from app.models.incident import (
    IncidentPriority,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)


class IncidentCreate(BaseModel):
    """Request used to create an operational incident."""

    title: str = Field(
        min_length=3,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=10_000,
    )

    severity: IncidentSeverity = (
        IncidentSeverity.WARNING
    )

    priority: IncidentPriority = (
        IncidentPriority.MEDIUM
    )

    source: IncidentSource = (
        IncidentSource.MANUAL
    )

    owner_id: int | None = Field(
        default=None,
        ge=1,
    )

    business_impact: str | None = Field(
        default=None,
        max_length=10_000,
    )

    started_at: datetime | None = None

    tags: list[str] = Field(
        default_factory=list,
        max_length=50,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    alert_ids: list[int] = Field(
        default_factory=list,
        max_length=500,
    )

    @field_validator(
        "title",
        "description",
        "business_impact",
    )
    @classmethod
    def normalize_text(
        cls,
        value: str | None,
    ) -> str | None:
        """Remove surrounding whitespace."""

        if value is None:
            return None

        normalized = value.strip()

        return normalized or None

    @field_validator("tags")
    @classmethod
    def normalize_tags(
        cls,
        value: list[str],
    ) -> list[str]:
        """Normalize and deduplicate tags."""

        normalized_tags: list[str] = []
        seen: set[str] = set()

        for tag in value:
            normalized = tag.strip().lower()

            if not normalized:
                continue

            if len(normalized) > 64:
                raise ValueError(
                    "each tag must contain at most "
                    "64 characters"
                )

            if normalized in seen:
                continue

            seen.add(normalized)
            normalized_tags.append(normalized)

        return normalized_tags

    @field_validator("alert_ids")
    @classmethod
    def deduplicate_alert_ids(
        cls,
        value: list[int],
    ) -> list[int]:
        """Validate and deduplicate alert identifiers."""

        if any(alert_id < 1 for alert_id in value):
            raise ValueError(
                "alert IDs must be greater than "
                "or equal to 1"
            )

        return list(
            dict.fromkeys(value)
        )


class IncidentUpdate(BaseModel):
    """Editable information excluding lifecycle state."""

    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=10_000,
    )

    severity: IncidentSeverity | None = None
    priority: IncidentPriority | None = None

    owner_id: int | None = Field(
        default=None,
        ge=1,
    )

    business_impact: str | None = Field(
        default=None,
        max_length=10_000,
    )

    root_cause: str | None = Field(
        default=None,
        max_length=10_000,
    )

    tags: list[str] | None = Field(
        default=None,
        max_length=50,
    )

    metadata: dict[str, Any] | None = None

    @field_validator(
        "title",
        "description",
        "business_impact",
        "root_cause",
    )
    @classmethod
    def normalize_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        return normalized or None

    @field_validator("tags")
    @classmethod
    def normalize_tags(
        cls,
        value: list[str] | None,
    ) -> list[str] | None:
        if value is None:
            return None

        normalized_tags: list[str] = []
        seen: set[str] = set()

        for tag in value:
            normalized = tag.strip().lower()

            if not normalized:
                continue

            if len(normalized) > 64:
                raise ValueError(
                    "each tag must contain at most "
                    "64 characters"
                )

            if normalized in seen:
                continue

            seen.add(normalized)
            normalized_tags.append(normalized)

        return normalized_tags


class IncidentResolveRequest(BaseModel):
    """Information required to resolve an incident."""

    resolution_summary: str = Field(
        min_length=3,
        max_length=10_000,
    )

    root_cause: str | None = Field(
        default=None,
        max_length=10_000,
    )

    @field_validator(
        "resolution_summary",
        "root_cause",
    )
    @classmethod
    def normalize_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        return normalized or None


class IncidentAlertAttachRequest(BaseModel):
    """Alerts to attach to an existing incident."""

    alert_ids: list[int] = Field(
        min_length=1,
        max_length=500,
    )

    @field_validator("alert_ids")
    @classmethod
    def validate_alert_ids(
        cls,
        value: list[int],
    ) -> list[int]:
        if any(alert_id < 1 for alert_id in value):
            raise ValueError(
                "alert IDs must be greater than "
                "or equal to 1"
            )

        return list(
            dict.fromkeys(value)
        )


class IncidentLifecycleTransition(BaseModel):
    """Explicit non-resolution lifecycle transition."""

    target_status: IncidentStatus

    @model_validator(mode="after")
    def reject_direct_resolution(
        self,
    ) -> "IncidentLifecycleTransition":
        if self.target_status == IncidentStatus.RESOLVED:
            raise ValueError(
                "use the incident resolution operation "
                "to resolve an incident"
            )

        return self


class IncidentAlertRead(BaseModel):
    """Alert evidence attached to an incident."""

    id: int
    device_id: int

    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus

    message: str
    occurrence_count: int = Field(ge=1)

    first_seen_at: datetime
    last_seen_at: datetime
    created_at: datetime
    resolved_at: datetime | None = None

    attached_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class IncidentSummary(BaseModel):
    """Compact incident representation."""

    id: int
    public_id: str

    title: str

    status: IncidentStatus
    severity: IncidentSeverity
    priority: IncidentPriority
    source: IncidentSource

    owner_id: int | None

    alert_count: int = Field(ge=0)

    started_at: datetime
    detected_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None

    created_at: datetime
    updated_at: datetime


class IncidentRead(BaseModel):
    """Complete incident response."""

    id: int
    public_id: str

    title: str
    description: str | None

    status: IncidentStatus
    severity: IncidentSeverity
    priority: IncidentPriority
    source: IncidentSource

    owner_id: int | None

    business_impact: str | None
    root_cause: str | None
    resolution_summary: str | None

    tags: list[str]
    metadata: dict[str, Any]

    started_at: datetime
    detected_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None

    created_at: datetime
    updated_at: datetime

    alerts: list[IncidentAlertRead] = Field(
        default_factory=list,
    )


class IncidentPaginationResponse(BaseModel):
    """Paginated incident query response."""

    items: list[IncidentSummary]

    total_count: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_pages: int = Field(ge=0)


class IncidentStatisticsResponse(BaseModel):
    """Operational statistics for one incident."""

    incident_id: int
    public_id: str

    alert_count: int = Field(ge=0)
    affected_device_count: int = Field(ge=0)

    duration_seconds: float = Field(ge=0)
    is_active: bool


class IncidentAlertAttachmentResponse(BaseModel):
    """Result of attaching alerts to an incident."""

    public_id: str

    requested_alert_count: int = Field(ge=0)
    attached_alert_count: int = Field(ge=0)

    alert_ids: list[int]


class IncidentAlertDetachResponse(BaseModel):
    """Result of detaching one alert."""

    public_id: str
    alert_id: int
    detached: bool