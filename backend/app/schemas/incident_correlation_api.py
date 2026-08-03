"""HTTP schemas for the Correlation Engine API."""

from pydantic import (
    BaseModel,
    Field,
)

from app.schemas.incident_correlation import (
    CorrelationEvaluationResult,
)


class CorrelationExecutionOptions(BaseModel):
    """Runtime options accepted by correlation commands."""

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


class CorrelationEvaluationResponse(
    CorrelationEvaluationResult
):
    """Persisted correlation evaluation returned over HTTP."""

    correlation_id: int = Field(
        ge=1,
    )

    persistence_created: bool