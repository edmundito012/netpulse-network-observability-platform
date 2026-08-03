"""Schemas for Correlation Engine analytics."""

from datetime import datetime

from pydantic import (
    BaseModel,
    Field,
)


class CorrelationAnalyticsCount(BaseModel):
    """One named analytics counter."""

    name: str
    count: int = Field(
        ge=0,
    )


class CorrelationAnalyticsRecentItem(BaseModel):
    """Compact representation of a recent correlation."""

    correlation_id: int = Field(
        ge=1,
    )

    source_alert_id: int = Field(
        ge=1,
    )

    target_incident_id: int | None = Field(
        default=None,
        ge=1,
    )

    outcome: str
    application_status: str
    signal_family: str

    score: float = Field(
        ge=0.0,
        le=1.0,
    )

    evaluated_at: datetime


class CorrelationAnalyticsSummary(BaseModel):
    """Operational summary of the Correlation Engine."""

    window_hours: int = Field(
        ge=1,
        le=720,
    )

    window_started_at: datetime
    generated_at: datetime

    total_evaluations: int = Field(
        ge=0,
    )

    applied_decisions: int = Field(
        ge=0,
    )

    failed_decisions: int = Field(
        ge=0,
    )

    pending_decisions: int = Field(
        ge=0,
    )

    incidents_created: int = Field(
        ge=0,
    )

    existing_incidents_matched: int = Field(
        ge=0,
    )

    no_action_decisions: int = Field(
        ge=0,
    )

    successful_decisions: int = Field(
        ge=0,
    )

    average_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    application_success_rate: float = Field(
        ge=0.0,
        le=100.0,
    )

    incident_reuse_rate: float = Field(
        ge=0.0,
        le=100.0,
    )

    estimated_incidents_avoided: int = Field(
        ge=0,
    )

    outcomes: list[CorrelationAnalyticsCount]
    application_statuses: list[CorrelationAnalyticsCount]
    signal_families: list[CorrelationAnalyticsCount]

    recent_correlations: list[
        CorrelationAnalyticsRecentItem
    ]