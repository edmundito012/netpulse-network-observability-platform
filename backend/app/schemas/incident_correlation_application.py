"""Schemas for applying persisted correlation decisions."""

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.core.correlation import (
    CorrelationApplicationStatus,
    CorrelationOutcome,
)


class CorrelationApplicationResult(BaseModel):
    """Result of applying one correlation decision."""

    correlation_id: int = Field(
        ge=1,
    )

    source_alert_id: int = Field(
        ge=1,
    )

    outcome: CorrelationOutcome

    application_status: (
        CorrelationApplicationStatus
    )

    incident_id: int | None = Field(
        default=None,
        ge=1,
    )

    incident_public_id: str | None = None

    incident_created: bool = False
    alert_attached: bool = False

    replayed: bool = False

    model_config = ConfigDict(
        use_enum_values=False,
    )