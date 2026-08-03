"""Pure input and output schemas for correlation scoring."""

from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.core.correlation import (
    CorrelationReason,
    CorrelationSignalFamily,
)
from app.models.alert import (
    AlertSeverity,
    AlertType,
)
from app.models.incident import (
    IncidentSeverity,
    IncidentStatus,
)


class CorrelationAlertSnapshot(BaseModel):
    """Minimal alert information required for scoring."""

    id: int = Field(
        ge=1,
    )

    device_id: int = Field(
        ge=1,
    )

    alert_type: AlertType

    severity: AlertSeverity

    observed_at: datetime

    model_config = ConfigDict(
        frozen=True,
    )

    @field_validator("observed_at")
    @classmethod
    def require_timezone(
        cls,
        value: datetime,
    ) -> datetime:
        """Require timezone-aware timestamps."""

        if (
            value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise ValueError(
                "observed_at must be timezone-aware"
            )

        return value


class CorrelationIncidentSnapshot(BaseModel):
    """Minimal candidate incident information required for scoring."""

    id: int = Field(
        ge=1,
    )

    public_id: str = Field(
        min_length=3,
        max_length=32,
    )

    status: IncidentStatus

    severity: IncidentSeverity

    detected_at: datetime

    latest_signal_at: datetime

    device_ids: frozenset[int] = Field(
        default_factory=frozenset,
    )

    alert_types: frozenset[AlertType] = Field(
        default_factory=frozenset,
    )

    model_config = ConfigDict(
        frozen=True,
    )

    @field_validator(
        "detected_at",
        "latest_signal_at",
    )
    @classmethod
    def require_timezone(
        cls,
        value: datetime,
    ) -> datetime:
        """Require timezone-aware timestamps."""

        if (
            value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise ValueError(
                "incident timestamps must be "
                "timezone-aware"
            )

        return value

    @field_validator("device_ids")
    @classmethod
    def validate_device_ids(
        cls,
        value: frozenset[int],
    ) -> frozenset[int]:
        """Reject invalid device identifiers."""

        if any(
            device_id < 1
            for device_id in value
        ):
            raise ValueError(
                "device_ids must contain positive "
                "identifiers"
            )

        return value


class CorrelationScoreComponents(BaseModel):
    """Individual contributions to a correlation score."""

    device: float = Field(
        ge=0.0,
        le=1.0,
    )

    temporal: float = Field(
        ge=0.0,
        le=1.0,
    )

    signal: float = Field(
        ge=0.0,
        le=1.0,
    )

    severity: float = Field(
        ge=0.0,
        le=1.0,
    )

    active_incident: float = Field(
        ge=0.0,
        le=1.0,
    )

    recent_detection: float = Field(
        ge=0.0,
        le=1.0,
    )

    model_config = ConfigDict(
        frozen=True,
    )


class CorrelationScoreBreakdown(BaseModel):
    """Explainable score for one candidate incident."""

    source_alert_id: int = Field(
        ge=1,
    )

    incident_id: int = Field(
        ge=1,
    )

    incident_public_id: str

    alert_family: CorrelationSignalFamily

    candidate_families: frozenset[
        CorrelationSignalFamily
    ] = Field(
        default_factory=frozenset,
    )

    score: float = Field(
        ge=0.0,
        le=1.0,
    )

    threshold: float = Field(
        ge=0.0,
        le=1.0,
    )

    accepted: bool

    blocked: bool

    reasons: list[CorrelationReason]

    components: CorrelationScoreComponents

    time_distance_seconds: float = Field(
        ge=0.0,
    )

    explanation: str

    model_config = ConfigDict(
        frozen=True,
    )