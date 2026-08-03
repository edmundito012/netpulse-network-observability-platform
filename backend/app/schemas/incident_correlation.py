"""Pydantic schemas for the Correlation Engine."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.core.correlation import (
    CorrelationApplicationStatus,
    CorrelationOutcome,
    CorrelationReason,
    CorrelationSignalFamily,
)


class CorrelationEvaluationRequest(BaseModel):
    """Request used to evaluate one alert for correlation."""

    source_alert_id: int = Field(
        ge=1,
    )

    window_seconds: int = Field(
        default=900,
        ge=60,
        le=86_400,
    )

    threshold: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
    )

    max_candidates: int = Field(
        default=25,
        ge=1,
        le=100,
    )

    apply_decision: bool = False


class IncidentCorrelationCreate(BaseModel):
    """Internal command used to persist a correlation decision."""

    correlation_key: str = Field(
        min_length=3,
        max_length=255,
    )

    source_alert_id: int = Field(
        ge=1,
    )

    target_incident_id: int | None = Field(
        default=None,
        ge=1,
    )

    outcome: CorrelationOutcome

    application_status: (
        CorrelationApplicationStatus
    ) = CorrelationApplicationStatus.EVALUATED

    signal_family: CorrelationSignalFamily

    score: Decimal = Field(
        ge=Decimal("0"),
        le=Decimal("1"),
        max_digits=5,
        decimal_places=4,
    )

    threshold: Decimal = Field(
        ge=Decimal("0"),
        le=Decimal("1"),
        max_digits=5,
        decimal_places=4,
    )

    reasons: list[CorrelationReason] = Field(
        default_factory=list,
        max_length=50,
    )

    candidate_count: int = Field(
        default=0,
        ge=0,
    )

    window_seconds: int = Field(
        ge=60,
        le=86_400,
    )

    explanation: str = Field(
        min_length=3,
        max_length=10_000,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    failure_reason: str | None = Field(
        default=None,
        max_length=10_000,
    )

    evaluated_at: datetime | None = None
    applied_at: datetime | None = None

    @field_validator(
        "correlation_key",
        "explanation",
        "failure_reason",
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

    @field_validator("reasons")
    @classmethod
    def deduplicate_reasons(
        cls,
        value: list[CorrelationReason],
    ) -> list[CorrelationReason]:
        """Preserve reason order while removing duplicates."""

        return list(
            dict.fromkeys(value)
        )

    @model_validator(mode="after")
    def validate_outcome_target(
        self,
    ) -> "IncidentCorrelationCreate":
        """Ensure the outcome and target incident agree."""

        if (
            self.outcome
            == CorrelationOutcome.MATCHED_EXISTING
            and self.target_incident_id is None
        ):
            raise ValueError(
                "MATCHED_EXISTING requires "
                "target_incident_id"
            )

        if (
            self.outcome
            != CorrelationOutcome.MATCHED_EXISTING
            and self.target_incident_id is not None
        ):
            raise ValueError(
                "target_incident_id is only valid for "
                "MATCHED_EXISTING"
            )

        if (
            self.application_status
            == CorrelationApplicationStatus.FAILED
            and self.failure_reason is None
        ):
            raise ValueError(
                "FAILED correlation decisions require "
                "failure_reason"
            )

        if (
            self.application_status
            == CorrelationApplicationStatus.APPLIED
            and self.applied_at is None
        ):
            raise ValueError(
                "APPLIED correlation decisions require "
                "applied_at"
            )

        return self


class CorrelationCandidateRead(BaseModel):
    """One scored incident candidate."""

    incident_id: int
    public_id: str

    score: float = Field(
        ge=0.0,
        le=1.0,
    )

    reasons: list[CorrelationReason]

    time_distance_seconds: float = Field(
        ge=0.0,
    )

    is_active: bool


class CorrelationEvaluationResult(BaseModel):
    """Explainable result produced before persistence."""

    source_alert_id: int

    outcome: CorrelationOutcome
    signal_family: CorrelationSignalFamily

    score: float = Field(
        ge=0.0,
        le=1.0,
    )

    threshold: float = Field(
        ge=0.0,
        le=1.0,
    )

    correlated: bool

    target_incident_id: int | None
    target_incident_public_id: str | None

    reasons: list[CorrelationReason]

    candidate_count: int = Field(
        ge=0,
    )

    window_seconds: int = Field(
        ge=60,
    )

    explanation: str

    candidates: list[
        CorrelationCandidateRead
    ] = Field(
        default_factory=list,
    )

    @model_validator(mode="after")
    def validate_correlated_result(
        self,
    ) -> "CorrelationEvaluationResult":
        """Ensure correlated results contain a target."""

        if self.correlated:
            if (
                self.outcome
                != CorrelationOutcome
                .MATCHED_EXISTING
            ):
                raise ValueError(
                    "correlated results must use "
                    "MATCHED_EXISTING"
                )

            if (
                self.target_incident_id is None
                or self.target_incident_public_id is None
            ):
                raise ValueError(
                    "correlated results require a "
                    "target incident"
                )

        return self


class IncidentCorrelationRead(BaseModel):
    """Persisted explainable correlation decision."""

    id: int
    correlation_key: str

    source_alert_id: int
    target_incident_id: int | None

    outcome: CorrelationOutcome

    application_status: (
        CorrelationApplicationStatus
    )

    signal_family: CorrelationSignalFamily

    score: Decimal
    threshold: Decimal

    reasons: list[CorrelationReason]

    candidate_count: int
    window_seconds: int

    explanation: str

    metadata: dict[str, Any] = Field(
        validation_alias=(
            "correlation_metadata"
        ),
    )

    failure_reason: str | None

    evaluated_at: datetime
    applied_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class IncidentCorrelationPaginationResponse(
    BaseModel
):
    """Paginated correlation history."""

    items: list[IncidentCorrelationRead]

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