"""Deterministic and explainable correlation scoring."""

from datetime import datetime
from math import isclose

from app.core.correlation import (
    CorrelationConfiguration,
    CorrelationReason,
    CorrelationSignalFamily,
)
from app.models.alert import AlertSeverity
from app.models.incident import (
    IncidentSeverity,
    IncidentStatus,
)
from app.schemas.incident_correlation_score import (
    CorrelationAlertSnapshot,
    CorrelationIncidentSnapshot,
    CorrelationScoreBreakdown,
    CorrelationScoreComponents,
)
from app.services.correlation_signal_service import (
    CorrelationSignalService,
)


class CorrelationScoringService:
    """Score an alert against one candidate incident."""

    _ACTIVE_STATUSES: frozenset[
        IncidentStatus
    ] = frozenset(
        {
            IncidentStatus.OPEN,
            IncidentStatus.ACKNOWLEDGED,
            IncidentStatus.INVESTIGATING,
            IncidentStatus.MONITORING,
        }
    )

    _ALERT_SEVERITY_RANK: dict[
        AlertSeverity,
        int,
    ] = {
        AlertSeverity.INFO: 1,
        AlertSeverity.WARNING: 2,
        AlertSeverity.CRITICAL: 3,
    }

    _INCIDENT_SEVERITY_RANK: dict[
        IncidentSeverity,
        int,
    ] = {
        IncidentSeverity.INFO: 1,
        IncidentSeverity.WARNING: 2,
        IncidentSeverity.CRITICAL: 3,
    }

    @classmethod
    def score(
        cls,
        *,
        alert: CorrelationAlertSnapshot,
        incident: CorrelationIncidentSnapshot,
        configuration: (
            CorrelationConfiguration
            | None
        ) = None,
    ) -> CorrelationScoreBreakdown:
        """Calculate one deterministic candidate score."""

        config = (
            configuration
            or CorrelationConfiguration()
        )

        reasons: list[CorrelationReason] = []

        alert_family = (
            CorrelationSignalService.classify(
                alert.alert_type
            )
        )

        candidate_families = (
            CorrelationSignalService.classify_many(
                incident.alert_types
            )
        )

        device_component = cls._score_device(
            alert=alert,
            incident=incident,
            configuration=config,
            reasons=reasons,
        )

        (
            temporal_component,
            time_distance_seconds,
        ) = cls._score_temporal_proximity(
            alert=alert,
            incident=incident,
            configuration=config,
            reasons=reasons,
        )

        signal_component = cls._score_signal(
            alert=alert,
            incident=incident,
            alert_family=alert_family,
            candidate_families=candidate_families,
            configuration=config,
            reasons=reasons,
        )

        severity_component = cls._score_severity(
            alert=alert,
            incident=incident,
            configuration=config,
            reasons=reasons,
        )

        active_component = cls._score_active_incident(
            incident=incident,
            configuration=config,
            reasons=reasons,
        )

        recent_component = cls._score_recent_detection(
            alert=alert,
            incident=incident,
            configuration=config,
            reasons=reasons,
        )

        raw_score = (
            device_component
            + temporal_component
            + signal_component
            + severity_component
            + active_component
            + recent_component
        )

        score = round(
            min(
                max(
                    raw_score,
                    0.0,
                ),
                1.0,
            ),
            4,
        )

        blocked = cls._is_blocked(
            reasons=reasons,
        )

        accepted = (
            not blocked
            and (
                score > config.threshold
                or isclose(
                    score,
                    config.threshold,
                    abs_tol=0.000001,
                )
            )
        )

        if (
            not accepted
            and CorrelationReason
            .SCORE_BELOW_THRESHOLD
            not in reasons
        ):
            reasons.append(
                CorrelationReason
                .SCORE_BELOW_THRESHOLD
            )

        components = CorrelationScoreComponents(
            device=round(
                device_component,
                4,
            ),
            temporal=round(
                temporal_component,
                4,
            ),
            signal=round(
                signal_component,
                4,
            ),
            severity=round(
                severity_component,
                4,
            ),
            active_incident=round(
                active_component,
                4,
            ),
            recent_detection=round(
                recent_component,
                4,
            ),
        )

        return CorrelationScoreBreakdown(
            source_alert_id=alert.id,
            incident_id=incident.id,
            incident_public_id=(
                incident.public_id
            ),
            alert_family=alert_family,
            candidate_families=(
                candidate_families
            ),
            score=score,
            threshold=config.threshold,
            accepted=accepted,
            blocked=blocked,
            reasons=reasons,
            components=components,
            time_distance_seconds=(
                time_distance_seconds
            ),
            explanation=cls._build_explanation(
                score=score,
                threshold=config.threshold,
                accepted=accepted,
                blocked=blocked,
                reasons=reasons,
            ),
        )

    @staticmethod
    def _score_device(
        *,
        alert: CorrelationAlertSnapshot,
        incident: CorrelationIncidentSnapshot,
        configuration: CorrelationConfiguration,
        reasons: list[CorrelationReason],
    ) -> float:
        """Score whether the incident contains the alert device."""

        if alert.device_id in incident.device_ids:
            reasons.append(
                CorrelationReason.SAME_DEVICE
            )

            return (
                configuration
                .weights
                .same_device
            )

        reasons.append(
            CorrelationReason.DEVICE_MISMATCH
        )

        return 0.0

    @staticmethod
    def _score_temporal_proximity(
        *,
        alert: CorrelationAlertSnapshot,
        incident: CorrelationIncidentSnapshot,
        configuration: CorrelationConfiguration,
        reasons: list[CorrelationReason],
    ) -> tuple[float, float]:
        """Score temporal distance using linear decay."""

        distance = CorrelationScoringService._distance_seconds(
            alert.observed_at,
            incident.latest_signal_at,
        )

        if distance > configuration.window_seconds:
            reasons.append(
                CorrelationReason
                .OUTSIDE_TEMPORAL_WINDOW
            )

            return (
                0.0,
                distance,
            )

        reasons.append(
            CorrelationReason
            .WITHIN_TEMPORAL_WINDOW
        )

        proximity_ratio = (
            1.0
            - (
                distance
                / configuration.window_seconds
            )
        )

        return (
            configuration
            .weights
            .temporal_proximity
            * proximity_ratio,
            distance,
        )

    @staticmethod
    def _score_signal(
        *,
        alert: CorrelationAlertSnapshot,
        incident: CorrelationIncidentSnapshot,
        alert_family: CorrelationSignalFamily,
        candidate_families: frozenset[
            CorrelationSignalFamily
        ],
        configuration: CorrelationConfiguration,
        reasons: list[CorrelationReason],
    ) -> float:
        """Score exact alert types and compatible families."""

        if alert.alert_type in incident.alert_types:
            reasons.append(
                CorrelationReason.SAME_ALERT_TYPE
            )

            reasons.append(
                CorrelationReason
                .COMPATIBLE_SIGNAL_FAMILY
            )

            return (
                configuration
                .weights
                .signal_compatibility
            )

        if (
            CorrelationSignalService
            .has_compatible_family(
                alert_family,
                candidate_families,
            )
        ):
            reasons.append(
                CorrelationReason
                .COMPATIBLE_SIGNAL_FAMILY
            )

            return (
                configuration
                .weights
                .signal_compatibility
            )

        reasons.append(
            CorrelationReason
            .INCOMPATIBLE_SIGNAL_FAMILY
        )

        return 0.0

    @staticmethod
    def _score_signal_families(
        *,
        alert: CorrelationAlertSnapshot,
        alert_family,
        candidate_families,
        configuration: CorrelationConfiguration,
        reasons: list[CorrelationReason],
    ) -> float:
        """Score compatible families."""

        del alert

        if alert_family in candidate_families:
            reasons.append(
                CorrelationReason
                .COMPATIBLE_SIGNAL_FAMILY
            )

            return (
                configuration
                .weights
                .signal_compatibility
            )

        if (
            CorrelationSignalService
            .has_compatible_family(
                alert_family,
                candidate_families,
            )
        ):
            reasons.append(
                CorrelationReason
                .COMPATIBLE_SIGNAL_FAMILY
            )

            return (
                configuration
                .weights
                .signal_compatibility
            )

        reasons.append(
            CorrelationReason
            .INCOMPATIBLE_SIGNAL_FAMILY
        )

        return 0.0

    @classmethod
    def _score_severity(
        cls,
        *,
        alert: CorrelationAlertSnapshot,
        incident: CorrelationIncidentSnapshot,
        configuration: CorrelationConfiguration,
        reasons: list[CorrelationReason],
    ) -> float:
        """Score exact or adjacent severity alignment."""

        alert_rank = cls._ALERT_SEVERITY_RANK[
            alert.severity
        ]

        incident_rank = cls._INCIDENT_SEVERITY_RANK[
            incident.severity
        ]

        difference = abs(
            alert_rank - incident_rank
        )

        if difference == 0:
            reasons.append(
                CorrelationReason
                .SEVERITY_ALIGNED
            )

            return (
                configuration
                .weights
                .severity_alignment
            )

        if difference == 1:
            return (
                configuration
                .weights
                .severity_alignment
                * 0.5
            )

        return 0.0

    @classmethod
    def _score_active_incident(
        cls,
        *,
        incident: CorrelationIncidentSnapshot,
        configuration: CorrelationConfiguration,
        reasons: list[CorrelationReason],
    ) -> float:
        """Score whether the candidate is active."""

        if (
            incident.status
            in cls._ACTIVE_STATUSES
        ):
            reasons.append(
                CorrelationReason
                .ACTIVE_INCIDENT_AVAILABLE
            )

            return (
                configuration
                .weights
                .active_incident
            )

        reasons.append(
            CorrelationReason
            .INCIDENT_ALREADY_RESOLVED
        )

        return 0.0

    @staticmethod
    def _score_recent_detection(
        *,
        alert: CorrelationAlertSnapshot,
        incident: CorrelationIncidentSnapshot,
        configuration: CorrelationConfiguration,
        reasons: list[CorrelationReason],
    ) -> float:
        """Score how recently the incident was detected."""

        distance = CorrelationScoringService._distance_seconds(
            alert.observed_at,
            incident.detected_at,
        )

        if distance > configuration.window_seconds:
            return 0.0

        reasons.append(
            CorrelationReason
            .INCIDENT_RECENTLY_DETECTED
        )

        recency_ratio = (
            1.0
            - (
                distance
                / configuration.window_seconds
            )
        )

        return (
            configuration
            .weights
            .recent_detection
            * recency_ratio
        )

    @staticmethod
    def _distance_seconds(
        first: datetime,
        second: datetime,
    ) -> float:
        """Return absolute temporal distance."""

        return abs(
            (
                first - second
            ).total_seconds()
        )

    @staticmethod
    def _is_blocked(
        *,
        reasons: list[CorrelationReason],
    ) -> bool:
        """Return whether a hard exclusion prevents correlation."""

        blockers = {
            CorrelationReason.DEVICE_MISMATCH,
            (
                CorrelationReason
                .OUTSIDE_TEMPORAL_WINDOW
            ),
            (
                CorrelationReason
                .INCIDENT_ALREADY_RESOLVED
            ),
        }

        return any(
            reason in blockers
            for reason in reasons
        )

    @staticmethod
    def _build_explanation(
        *,
        score: float,
        threshold: float,
        accepted: bool,
        blocked: bool,
        reasons: list[CorrelationReason],
    ) -> str:
        """Build a stable human-readable explanation."""

        reason_text = ", ".join(
            reason.value
            for reason in reasons
        )

        if accepted:
            decision = (
                "candidate accepted"
            )
        elif blocked:
            decision = (
                "candidate rejected by a hard rule"
            )
        else:
            decision = (
                "candidate rejected below threshold"
            )

        return (
            f"{decision}; score={score:.4f}; "
            f"threshold={threshold:.4f}; "
            f"reasons=[{reason_text}]"
        )