"""Schemas for the public Incident Operations portfolio dashboard."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.incident import (
    IncidentPriority,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)


class IncidentPortfolioItem(BaseModel):
    """Compact incident shown in the portfolio dashboard."""

    public_id: str
    title: str

    status: IncidentStatus
    severity: IncidentSeverity
    priority: IncidentPriority
    source: IncidentSource

    alert_count: int = Field(ge=0)

    started_at: datetime
    detected_at: datetime

    duration_seconds: float = Field(ge=0)


class IncidentPortfolioSummary(BaseModel):
    """Operational aggregate displayed by the portfolio dashboard."""

    total_incidents: int = Field(ge=0)
    active_incidents: int = Field(ge=0)
    critical_incidents: int = Field(ge=0)

    open_incidents: int = Field(ge=0)
    acknowledged_incidents: int = Field(ge=0)
    investigating_incidents: int = Field(ge=0)
    monitoring_incidents: int = Field(ge=0)
    resolved_incidents: int = Field(ge=0)

    correlated_alerts: int = Field(ge=0)
    affected_devices: int = Field(ge=0)

    mean_resolution_seconds: float | None

    latest_incidents: list[IncidentPortfolioItem]