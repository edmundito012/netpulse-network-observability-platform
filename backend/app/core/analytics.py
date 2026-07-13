"""Shared analytics domain types.

This module contains stable enums used across analytics APIs, services,
schemas, and repositories. Keeping these values centralized prevents
inconsistent string literals across the platform.
"""

from enum import Enum


class MetricName(str, Enum):
    """Metrics supported by the historical analytics foundation."""

    LATENCY = "latency"
    JITTER = "jitter"
    PACKET_LOSS = "packet_loss"


class MissingValuePolicy(str, Enum):
    """Strategy used when a metric sample has no measured value."""

    DROP = "drop"
    PRESERVE = "preserve"


class SortDirection(str, Enum):
    """Ordering applied when retrieving historical metric samples."""

    ASCENDING = "asc"
    DESCENDING = "desc"


class AnalyticsSeverity(str, Enum):
    """Normalized severity levels shared by analytics engines."""

    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class ConfidenceLevel(str, Enum):
    """Normalized confidence levels shared by analytics engines."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class BurstStatus(str, Enum):
    """Lifecycle status of a detected metric burst."""

    COMPLETED = "COMPLETED"
    ACTIVE = "ACTIVE"