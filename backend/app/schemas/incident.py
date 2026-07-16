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

    source: IncidentSource = IncidentSource.MANUAL

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
        """Remove surrounding whitespace from user-provided text."""

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
        """Normalize tags and remove duplicates while preserving order."""

        normalized_tags: list[str] = []
        seen: set[str] = set()

        for tag in value:
            normalized = tag.strip().lower()

            if not normalized or normalized in seen:
                continue

            if len(normalized) > 64:
                raise ValueError(
                    "each tag must contain at most 64 characters"
                )

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
                "alert IDs must be greater than or equal to 1"
            )

        return list(dict.fromkeys(value))


class IncidentUpdate(BaseModel):
    """Editable incident information excluding lifecycle transitions."""

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

            if not normalized or normalized in seen:
                continue

            if len(normalized) > 64:
                raise ValueError(
                    "each tag must contain at most 64 characters"
                )

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
                "alert IDs must be greater than or equal to 1"
            )

        return list(dict.fromkeys(value))


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
    """Compact incident representation for lists and dashboards."""

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

    model_config = ConfigDict(
        from_attributes=True,
    )


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

    model_config = ConfigDict(
        from_attributes=True,
    )


class IncidentLifecycleTransition(BaseModel):
    """Explicit target status for controlled lifecycle operations."""

    target_status: IncidentStatus

    @model_validator(mode="after")
    def reject_direct_resolution(
        self,
    ) -> "IncidentLifecycleTransition":
        """Require resolution details through the dedicated operation."""

        if self.target_status == IncidentStatus.RESOLVED:
            raise ValueError(
                "use the incident resolution operation "
                "to resolve an incident"
            )

        return self