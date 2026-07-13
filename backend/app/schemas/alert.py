"""Schemas for operational alerts."""

from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.models.alert import (
    AlertSeverity,
    AlertStatus,
    AlertType,
)


class AlertRead(BaseModel):
    """Public alert representation."""

    id: int
    device_id: int

    alert_type: AlertType
    deduplication_key: str

    severity: AlertSeverity
    status: AlertStatus

    message: str

    occurrence_count: int = Field(
        ge=1,
    )

    created_at: datetime
    first_seen_at: datetime
    last_seen_at: datetime

    resolved_at: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )