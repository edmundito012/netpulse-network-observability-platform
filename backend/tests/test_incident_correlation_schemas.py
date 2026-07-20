"""Unit tests for Correlation Engine schemas."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core.correlation import (
    CorrelationApplicationStatus,
    CorrelationOutcome,
    CorrelationReason,
    CorrelationSignalFamily,
)
from app.schemas.incident_correlation import (
    CorrelationEvaluationRequest,
    CorrelationEvaluationResult,
    IncidentCorrelationCreate,
    IncidentCorrelationRead,
)


NOW = datetime(
    2026,
    7,
    18,
    12,
    0,
    tzinfo=UTC,
)


def test_evaluation_request_defaults() -> None:
    payload = CorrelationEvaluationRequest(
        source_alert_id=42,
    )

    assert payload.window_seconds == 900
    assert payload.threshold == 0.65
    assert payload.max_candidates == 25
    assert payload.apply_decision is False


@pytest.mark.parametrize(
    (
        "field_name",
        "field_value",
    ),
    [
        (
            "source_alert_id",
            0,
        ),
        (
            "window_seconds",
            59,
        ),
        (
            "window_seconds",
            86_401,
        ),
        (
            "threshold",
            -0.01,
        ),
        (
            "threshold",
            1.01,
        ),
        (
            "max_candidates",
            0,
        ),
        (
            "max_candidates",
            101,
        ),
    ],
)
def test_evaluation_request_rejects_invalid_values(
    field_name: str,
    field_value: int | float,
) -> None:
    data = {
        "source_alert_id": 42,
    }

    data[field_name] = field_value

    with pytest.raises(ValidationError):
        CorrelationEvaluationRequest(
            **data
        )


def test_create_normalizes_and_deduplicates() -> None:
    payload = IncidentCorrelationCreate(
        correlation_key=(
            "  alert:42:incident:7:window:900  "
        ),
        source_alert_id=42,
        target_incident_id=7,
        outcome=(
            CorrelationOutcome.MATCHED_EXISTING
        ),
        signal_family=(
            CorrelationSignalFamily.CONNECTIVITY
        ),
        score=Decimal("0.8800"),
        threshold=Decimal("0.6500"),
        reasons=[
            CorrelationReason.SAME_DEVICE,
            CorrelationReason.SAME_DEVICE,
            (
                CorrelationReason
                .WITHIN_TEMPORAL_WINDOW
            ),
        ],
        candidate_count=3,
        window_seconds=900,
        explanation=(
            "  Strong candidate correlation  "
        ),
    )

    assert payload.correlation_key == (
        "alert:42:incident:7:window:900"
    )

    assert payload.explanation == (
        "Strong candidate correlation"
    )

    assert payload.reasons == [
        CorrelationReason.SAME_DEVICE,
        (
            CorrelationReason
            .WITHIN_TEMPORAL_WINDOW
        ),
    ]


def test_matched_existing_requires_target() -> None:
    with pytest.raises(
        ValidationError,
        match="requires target_incident_id",
    ):
        IncidentCorrelationCreate(
            correlation_key="alert:42:matched",
            source_alert_id=42,
            outcome=(
                CorrelationOutcome
                .MATCHED_EXISTING
            ),
            signal_family=(
                CorrelationSignalFamily
                .CONNECTIVITY
            ),
            score=Decimal("0.8000"),
            threshold=Decimal("0.6500"),
            window_seconds=900,
            explanation="Strong match",
        )


@pytest.mark.parametrize(
    "outcome",
    [
        CorrelationOutcome.CREATE_NEW,
        CorrelationOutcome.NO_ACTION,
    ],
)
def test_non_matching_outcome_rejects_target(
    outcome: CorrelationOutcome,
) -> None:
    with pytest.raises(
        ValidationError,
        match=(
            "target_incident_id is only valid"
        ),
    ):
        IncidentCorrelationCreate(
            correlation_key="alert:42:no-target",
            source_alert_id=42,
            target_incident_id=7,
            outcome=outcome,
            signal_family=(
                CorrelationSignalFamily
                .CONNECTIVITY
            ),
            score=Decimal("0.4000"),
            threshold=Decimal("0.6500"),
            window_seconds=900,
            explanation="No existing match",
        )


def test_failed_decision_requires_reason() -> None:
    with pytest.raises(
        ValidationError,
        match="require failure_reason",
    ):
        IncidentCorrelationCreate(
            correlation_key="alert:42:failed",
            source_alert_id=42,
            outcome=CorrelationOutcome.NO_ACTION,
            application_status=(
                CorrelationApplicationStatus.FAILED
            ),
            signal_family=(
                CorrelationSignalFamily.GENERIC
            ),
            score=Decimal("0.0000"),
            threshold=Decimal("0.6500"),
            window_seconds=900,
            explanation="Evaluation failed",
        )


def test_applied_decision_requires_timestamp() -> None:
    with pytest.raises(
        ValidationError,
        match="require applied_at",
    ):
        IncidentCorrelationCreate(
            correlation_key="alert:42:applied",
            source_alert_id=42,
            outcome=CorrelationOutcome.CREATE_NEW,
            application_status=(
                CorrelationApplicationStatus.APPLIED
            ),
            signal_family=(
                CorrelationSignalFamily.GENERIC
            ),
            score=Decimal("0.0000"),
            threshold=Decimal("0.6500"),
            window_seconds=900,
            explanation="Created a new incident",
        )


def test_correlated_result_requires_target() -> None:
    with pytest.raises(
        ValidationError,
        match="require a target incident",
    ):
        CorrelationEvaluationResult(
            source_alert_id=42,
            outcome=(
                CorrelationOutcome.MATCHED_EXISTING
            ),
            signal_family=(
                CorrelationSignalFamily
                .CONNECTIVITY
            ),
            score=0.88,
            threshold=0.65,
            correlated=True,
            target_incident_id=None,
            target_incident_public_id=None,
            reasons=[
                CorrelationReason.SAME_DEVICE,
            ],
            candidate_count=1,
            window_seconds=900,
            explanation="Candidate selected",
        )


def test_read_schema_maps_orm_metadata() -> None:
    class CorrelationStub:
        id = 1
        correlation_key = (
            "alert:42:incident:7:window:900"
        )

        source_alert_id = 42
        target_incident_id = 7

        outcome = (
            CorrelationOutcome.MATCHED_EXISTING
        )

        application_status = (
            CorrelationApplicationStatus.APPLIED
        )

        signal_family = (
            CorrelationSignalFamily.CONNECTIVITY
        )

        score = Decimal("0.8800")
        threshold = Decimal("0.6500")

        reasons = [
            CorrelationReason.SAME_DEVICE.value,
        ]

        candidate_count = 2
        window_seconds = 900

        explanation = "Strong match"

        correlation_metadata = {
            "engine_version": "1.0",
        }

        failure_reason = None
        evaluated_at = NOW
        applied_at = NOW

    result = (
        IncidentCorrelationRead
        .model_validate(
            CorrelationStub()
        )
    )

    assert result.id == 1

    assert result.metadata == {
        "engine_version": "1.0",
    }

    assert result.reasons == [
        CorrelationReason.SAME_DEVICE,
    ]