"""Schemas for temporal metric series."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.analytics import (
    MetricName,
    MissingValuePolicy,
    SortDirection,
)


class MetricSeriesSample(BaseModel):
    """Single timestamped metric sample."""

    model_config = ConfigDict(from_attributes=True)

    metric_id: int
    device_id: int
    checked_at: datetime
    value: float | None


class MetricSeriesResponse(BaseModel):
    """Historical series returned for a device metric window."""

    device_id: int
    metric_name: MetricName

    start_at: datetime | None
    end_at: datetime | None

    requested_limit: int
    sort_direction: SortDirection
    missing_value_policy: MissingValuePolicy

    database_sample_count: int = Field(ge=0)
    returned_sample_count: int = Field(ge=0)
    missing_sample_count: int = Field(ge=0)

    samples: list[MetricSeriesSample]