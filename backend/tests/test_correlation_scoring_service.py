"""Tests for deterministic correlation scoring."""

from datetime import (
    UTC,
    datetime,
    timedelta,
)

import pytest

from app.core.correlation import (
    CorrelationConfiguration,
    CorrelationReason,
    CorrelationScoringWeights,
    CorrelationSignalFamily,
)
from app.models.alert import (
    AlertSeverity,
    AlertType,
)
from app.models.incident import (
    IncidentSeverity,
    IncidentStatus,
)
from app.schemas.incident_correlation_score import (
    CorrelationAlertSnapshot,
    CorrelationIncidentSnapshot,
)
from app.services.correlation_scoring_service import (
    CorrelationScoringService,
)


NOW = datetime(
    2026,
    7,
    20,
    12,
    0,
    tzinfo=UTC,
)


def build_alert(
    *,
    alert_id: int = 42,
    device_id: int = 10,
    alert_type: AlertType = (
        AlertType.PACKET_LOSS
    ),
    severity: AlertSeverity = (
        AlertSeverity.CRITICAL
    ),
    observed_at: datetime = NOW,
) -> CorrelationAlertSnapshot:
    """Build a source alert snapshot."""

    return CorrelationAlertSnapshot(
        id=alert_id,
        device_id=device_id,
        alert_type=alert_type,
        severity=severity,
        observed_at=observed_at,
    )


def build_incident(
    *,
    incident_id: int = 7,
    public_id: str = "INC-2026-000007",
    status: IncidentStatus = (
        IncidentStatus.INVESTIGATING
    ),
    severity: IncidentSeverity = (
        IncidentSeverity.CRITICAL
    ),
    detected_at: datetime = NOW,
    latest_signal_at: datetime = NOW,
    device_ids: frozenset[int] = frozenset(
        {
            10,
        }
    ),
    alert_types: frozenset[
        AlertType
    ] = frozenset(
        {
            AlertType.PACKET_LOSS_BURST,
        }
    ),
) -> CorrelationIncidentSnapshot:
    """Build a candidate incident snapshot."""

    return CorrelationIncidentSnapshot(
        id=incident_id,
        public_id=public_id,
        status=status,
        severity=severity,
        detected_at=detected_at,
        latest_signal_at=latest_signal_at,
        device_ids=device_ids,
        alert_types=alert_types,
    )


def test_strong_candidate_is_accepted() -> None:
    result = CorrelationScoringService.score(
        alert=build_alert(),
        incident=build_incident(),
    )

    assert result.score == 1.0
    assert result.accepted is True
    assert result.blocked is False

    assert (
        CorrelationReason.SAME_DEVICE
        in result.reasons
    )

    assert (
        CorrelationReason
        .WITHIN_TEMPORAL_WINDOW
        in result.reasons
    )

    assert (
        CorrelationReason
        .COMPATIBLE_SIGNAL_FAMILY
        in result.reasons
    )

    assert (
        CorrelationReason
        .SEVERITY_ALIGNED
        in result.reasons
    )

    assert (
        CorrelationReason
        .ACTIVE_INCIDENT_AVAILABLE
        in result.reasons
    )

    assert (
        CorrelationReason
        .INCIDENT_RECENTLY_DETECTED
        in result.reasons
    )


def test_exact_alert_type_is_explained() -> None:
    result = CorrelationScoringService.score(
        alert=build_alert(),
        incident=build_incident(
            alert_types=frozenset(
                {
                    AlertType.PACKET_LOSS,
                }
            )
        ),
    )

    assert (
        CorrelationReason.SAME_ALERT_TYPE
        in result.reasons
    )

    assert result.accepted is True


def test_compatible_signal_families_score() -> None:
    result = CorrelationScoringService.score(
        alert=build_alert(
            alert_type=AlertType.PACKET_LOSS,
        ),
        incident=build_incident(
            alert_types=frozenset(
                {
                    AlertType.LATENCY_TREND,
                }
            )
        ),
    )

    assert (
        result.alert_family
        == CorrelationSignalFamily.CONNECTIVITY
    )

    assert (
        CorrelationSignalFamily.PERFORMANCE
        in result.candidate_families
    )

    assert (
        CorrelationReason
        .COMPATIBLE_SIGNAL_FAMILY
        in result.reasons
    )


def test_incompatible_signal_family_scores_zero() -> None:
    result = CorrelationScoringService.score(
        alert=build_alert(
            alert_type=AlertType.PREDICTIVE,
        ),
        incident=build_incident(
            alert_types=frozenset(
                {
                    AlertType.FLAPPING,
                }
            )
        ),
    )

    assert result.components.signal == 0.0

    assert (
        CorrelationReason
        .INCOMPATIBLE_SIGNAL_FAMILY
        in result.reasons
    )


def test_device_mismatch_is_hard_blocker() -> None:
    result = CorrelationScoringService.score(
        alert=build_alert(
            device_id=99,
        ),
        incident=build_incident(),
    )

    assert result.accepted is False
    assert result.blocked is True

    assert (
        CorrelationReason.DEVICE_MISMATCH
        in result.reasons
    )

    assert (
        CorrelationReason
        .SCORE_BELOW_THRESHOLD
        in result.reasons
    )


def test_outside_window_is_hard_blocker() -> None:
    result = CorrelationScoringService.score(
        alert=build_alert(),
        incident=build_incident(
            latest_signal_at=(
                NOW
                - timedelta(
                    seconds=901,
                )
            )
        ),
    )

    assert result.accepted is False
    assert result.blocked is True

    assert (
        CorrelationReason
        .OUTSIDE_TEMPORAL_WINDOW
        in result.reasons
    )


def test_exact_window_boundary_is_allowed() -> None:
    result = CorrelationScoringService.score(
        alert=build_alert(),
        incident=build_incident(
            latest_signal_at=(
                NOW
                - timedelta(
                    seconds=900,
                )
            )
        ),
    )

    assert (
        CorrelationReason
        .WITHIN_TEMPORAL_WINDOW
        in result.reasons
    )

    assert (
        CorrelationReason
        .OUTSIDE_TEMPORAL_WINDOW
        not in result.reasons
    )

    assert result.blocked is False


def test_resolved_incident_is_hard_blocker() -> None:
    result = CorrelationScoringService.score(
        alert=build_alert(),
        incident=build_incident(
            status=IncidentStatus.RESOLVED,
        ),
    )

    assert result.accepted is False
    assert result.blocked is True

    assert (
        CorrelationReason
        .INCIDENT_ALREADY_RESOLVED
        in result.reasons
    )


def test_temporal_component_decays_linearly() -> None:
    result = CorrelationScoringService.score(
        alert=build_alert(),
        incident=build_incident(
            latest_signal_at=(
                NOW
                - timedelta(
                    seconds=450,
                )
            )
        ),
    )

    assert result.components.temporal == (
        pytest.approx(
            0.10,
        )
    )

    assert result.time_distance_seconds == (
        450.0
    )


def test_adjacent_severity_receives_half_credit() -> None:
    result = CorrelationScoringService.score(
        alert=build_alert(
            severity=AlertSeverity.CRITICAL,
        ),
        incident=build_incident(
            severity=IncidentSeverity.WARNING,
        ),
    )

    assert result.components.severity == (
        pytest.approx(
            0.05,
        )
    )

    assert (
        CorrelationReason
        .SEVERITY_ALIGNED
        not in result.reasons
    )


def test_opposite_severity_receives_no_credit() -> None:
    result = CorrelationScoringService.score(
        alert=build_alert(
            severity=AlertSeverity.CRITICAL,
        ),
        incident=build_incident(
            severity=IncidentSeverity.INFO,
        ),
    )

    assert result.components.severity == 0.0


def test_score_equal_to_threshold_is_accepted() -> None:
    configuration = CorrelationConfiguration(
        threshold=0.65,
        weights=CorrelationScoringWeights(
            same_device=0.35,
            temporal_proximity=0.20,
            signal_compatibility=0.10,
            severity_alignment=0.00,
            active_incident=0.00,
            recent_detection=0.35,
        ),
    )

    result = CorrelationScoringService.score(
        alert=build_alert(),
        incident=build_incident(
            detected_at=(
                NOW
                - timedelta(
                    seconds=901,
                )
            ),
            latest_signal_at=NOW,
        ),
        configuration=configuration,
    )

    assert result.score == 0.65
    assert result.threshold == 0.65
    assert result.accepted is True


def test_score_below_threshold_is_rejected() -> None:
    configuration = CorrelationConfiguration(
        threshold=0.6501,
        weights=CorrelationScoringWeights(
            same_device=0.35,
            temporal_proximity=0.20,
            signal_compatibility=0.10,
            severity_alignment=0.00,
            active_incident=0.00,
            recent_detection=0.35,
        ),
    )

    result = CorrelationScoringService.score(
        alert=build_alert(),
        incident=build_incident(
            detected_at=(
                NOW
                - timedelta(
                    seconds=901,
                )
            ),
            latest_signal_at=NOW,
        ),
        configuration=configuration,
    )

    assert result.score == 0.65
    assert result.accepted is False
    assert result.blocked is False

    assert (
        CorrelationReason
        .SCORE_BELOW_THRESHOLD
        in result.reasons
    )


def test_result_contains_component_total() -> None:
    result = CorrelationScoringService.score(
        alert=build_alert(),
        incident=build_incident(),
    )

    component_total = (
        result.components.device
        + result.components.temporal
        + result.components.signal
        + result.components.severity
        + result.components.active_incident
        + result.components.recent_detection
    )

    assert result.score == pytest.approx(
        component_total
    )


def test_explanation_contains_decision_and_score() -> None:
    result = CorrelationScoringService.score(
        alert=build_alert(),
        incident=build_incident(),
    )

    assert "candidate accepted" in (
        result.explanation
    )

    assert "score=1.0000" in (
        result.explanation
    )

    assert "threshold=0.6500" in (
        result.explanation
    )