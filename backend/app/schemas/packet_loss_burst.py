"""Schemas for packet loss burst analytics."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.core.analytics import (
    AnalyticsSeverity,
    BurstStatus,
)


class PacketLossBurstRead(BaseModel):
    """One detected packet loss burst."""

    start_at: datetime
    end_at: datetime

    duration_seconds: float = Field(ge=0)
    sample_count: int = Field(ge=1)

    average_packet_loss_percent: float = Field(
        ge=0,
        le=100,
    )
    peak_packet_loss_percent: float = Field(
        ge=0,
        le=100,
    )

    severity: AnalyticsSeverity
    status: BurstStatus


class PacketLossBurstResponse(BaseModel):
    """Packet loss burst analysis response."""

    device_id: int | None

    start_at: datetime | None
    end_at: datetime | None

    burst_detected: bool
    current_burst_active: bool

    severity: AnalyticsSeverity

    samples_analyzed: int = Field(ge=0)
    measured_samples: int = Field(ge=0)
    missing_samples: int = Field(ge=0)

    burst_count: int = Field(ge=0)
    longest_burst_samples: int = Field(ge=0)

    peak_packet_loss_percent: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    average_packet_loss_percent: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    warning_threshold_percent: float = Field(
        ge=0,
        le=100,
    )
    critical_threshold_percent: float = Field(
        ge=0,
        le=100,
    )
    minimum_consecutive_samples: int = Field(ge=2)
    maximum_gap_seconds: int = Field(ge=1)

    bursts: list[PacketLossBurstRead]