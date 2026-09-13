"""Shared analytics domain types.

This module contains stable enums used across analytics APIs, services,
schemas, and repositories. Keeping these values centralized prevents
inconsistent string literals across the platform.
"""

from enum import StrEnum


class MetricName(StrEnum):
    """Metrics supported by the historical analytics foundation."""

    LATENCY = "latency"
    JITTER = "jitter"
    PACKET_LOSS = "packet_loss"


class MissingValuePolicy(StrEnum):
    """Strategy used when a metric sample has no measured value."""

    DROP = "drop"
    PRESERVE = "preserve"


class SortDirection(StrEnum):
    """Ordering applied when retrieving historical metric samples."""

    ASCENDING = "asc"
    DESCENDING = "desc"


class AnalyticsSeverity(StrEnum):
    """Normalized severity levels shared by analytics engines."""

    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class ConfidenceLevel(StrEnum):
    """Normalized confidence levels shared by analytics engines."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class BurstStatus(StrEnum):
    """Lifecycle status of a detected metric burst."""

    COMPLETED = "COMPLETED"
    ACTIVE = "ACTIVE"
