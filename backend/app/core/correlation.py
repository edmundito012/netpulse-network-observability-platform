"""Core enums and configuration for alert correlation."""

from dataclasses import dataclass
from enum import Enum


class CorrelationOutcome(str, Enum):
    """Decision produced by the Correlation Engine."""

    MATCHED_EXISTING = "MATCHED_EXISTING"
    CREATE_NEW = "CREATE_NEW"
    NO_ACTION = "NO_ACTION"


class CorrelationApplicationStatus(str, Enum):
    """Persistence state of a correlation decision."""

    EVALUATED = "EVALUATED"
    APPLIED = "APPLIED"
    FAILED = "FAILED"


class CorrelationSignalFamily(str, Enum):
    """Functional family used to compare related signals."""

    CONNECTIVITY = "CONNECTIVITY"
    PERFORMANCE = "PERFORMANCE"
    STABILITY = "STABILITY"
    EXPERIENCE = "EXPERIENCE"
    PREDICTIVE = "PREDICTIVE"
    GENERIC = "GENERIC"


class CorrelationReason(str, Enum):
    """Explainable reason contributing to a correlation score."""

    SAME_DEVICE = "SAME_DEVICE"
    WITHIN_TEMPORAL_WINDOW = "WITHIN_TEMPORAL_WINDOW"
    COMPATIBLE_SIGNAL_FAMILY = "COMPATIBLE_SIGNAL_FAMILY"
    SAME_ALERT_TYPE = "SAME_ALERT_TYPE"
    SEVERITY_ALIGNED = "SEVERITY_ALIGNED"
    ACTIVE_INCIDENT_AVAILABLE = "ACTIVE_INCIDENT_AVAILABLE"
    INCIDENT_RECENTLY_DETECTED = "INCIDENT_RECENTLY_DETECTED"
    SHARED_ALERT_EVIDENCE = "SHARED_ALERT_EVIDENCE"

    DEVICE_MISMATCH = "DEVICE_MISMATCH"
    OUTSIDE_TEMPORAL_WINDOW = "OUTSIDE_TEMPORAL_WINDOW"
    INCOMPATIBLE_SIGNAL_FAMILY = "INCOMPATIBLE_SIGNAL_FAMILY"
    INCIDENT_ALREADY_RESOLVED = "INCIDENT_ALREADY_RESOLVED"
    SCORE_BELOW_THRESHOLD = "SCORE_BELOW_THRESHOLD"
    NO_CANDIDATE_INCIDENT = "NO_CANDIDATE_INCIDENT"


@dataclass(frozen=True, slots=True)
class CorrelationScoringWeights:
    """Weights used by the deterministic scoring engine."""

    same_device: float = 0.35
    temporal_proximity: float = 0.20
    signal_compatibility: float = 0.20
    severity_alignment: float = 0.10
    active_incident: float = 0.10
    recent_detection: float = 0.05

    def __post_init__(self) -> None:
        """Validate individual weights and their total."""

        values = (
            self.same_device,
            self.temporal_proximity,
            self.signal_compatibility,
            self.severity_alignment,
            self.active_incident,
            self.recent_detection,
        )

        if any(
            value < 0.0 or value > 1.0
            for value in values
        ):
            raise ValueError(
                "correlation weights must be between "
                "0.0 and 1.0"
            )

        total = sum(values)

        if abs(total - 1.0) > 0.000001:
            raise ValueError(
                "correlation weights must add up to 1.0"
            )


@dataclass(frozen=True, slots=True)
class CorrelationConfiguration:
    """Runtime configuration for one correlation evaluation."""

    window_seconds: int = 900
    threshold: float = 0.65
    max_candidates: int = 25

    weights: CorrelationScoringWeights = (
        CorrelationScoringWeights()
    )

    def __post_init__(self) -> None:
        """Reject unsafe or meaningless configuration."""

        if (
            self.window_seconds < 60
            or self.window_seconds > 86_400
        ):
            raise ValueError(
                "window_seconds must be between "
                "60 and 86400"
            )

        if (
            self.threshold < 0.0
            or self.threshold > 1.0
        ):
            raise ValueError(
                "threshold must be between "
                "0.0 and 1.0"
            )

        if (
            self.max_candidates < 1
            or self.max_candidates > 100
        ):
            raise ValueError(
                "max_candidates must be between "
                "1 and 100"
            )