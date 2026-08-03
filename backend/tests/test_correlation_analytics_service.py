"""Tests for Correlation Engine analytics."""

from datetime import (
    UTC,
    datetime,
)
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from app.services.correlation_analytics_service import (
    CorrelationAnalyticsService,
)


NOW = datetime(
    2026,
    8,
    3,
    12,
    0,
    tzinfo=UTC,
)


@patch(
    "app.services.correlation_analytics_service."
    "CorrelationAnalyticsRepository.get_recent"
)
@patch(
    "app.services.correlation_analytics_service."
    "CorrelationAnalyticsRepository.count_by_column"
)
@patch(
    "app.services.correlation_analytics_service."
    "CorrelationAnalyticsRepository.get_totals"
)
def test_get_summary_calculates_rates(
    totals_mock,
    counts_mock,
    recent_mock,
) -> None:
    """Calculate success and incident reuse percentages."""

    totals_mock.return_value = {
        "total_evaluations": 10,
        "applied_decisions": 8,
        "failed_decisions": 2,
        "pending_decisions": 0,
        "incidents_created": 3,
        "existing_incidents_matched": 5,
        "no_action_decisions": 2,
        "average_score": 0.81234,
    }

    counts_mock.return_value = [
        (
            "MATCHED_EXISTING",
            5,
        ),
    ]

    recent_mock.return_value = []

    result = (
        CorrelationAnalyticsService
        .get_summary(
            db=SimpleNamespace(),
            window_hours=24,
            recent_limit=20,
        )
    )

    assert result.total_evaluations == 10
    assert result.successful_decisions == 8

    assert (
        result.application_success_rate
        == 80.0
    )

    assert result.incident_reuse_rate == 62.5

    assert (
        result.estimated_incidents_avoided
        == 5
    )

    assert result.average_score == 0.8123


@patch(
    "app.services.correlation_analytics_service."
    "CorrelationAnalyticsRepository.get_recent"
)
@patch(
    "app.services.correlation_analytics_service."
    "CorrelationAnalyticsRepository.count_by_column"
)
@patch(
    "app.services.correlation_analytics_service."
    "CorrelationAnalyticsRepository.get_totals"
)
def test_get_summary_handles_empty_database(
    totals_mock,
    counts_mock,
    recent_mock,
) -> None:
    """Return zero rates when no correlations exist."""

    totals_mock.return_value = {
        "total_evaluations": 0,
        "applied_decisions": 0,
        "failed_decisions": 0,
        "pending_decisions": 0,
        "incidents_created": 0,
        "existing_incidents_matched": 0,
        "no_action_decisions": 0,
        "average_score": None,
    }

    counts_mock.return_value = []
    recent_mock.return_value = []

    result = (
        CorrelationAnalyticsService
        .get_summary(
            db=SimpleNamespace(),
        )
    )

    assert result.total_evaluations == 0
    assert result.average_score is None

    assert (
        result.application_success_rate
        == 0.0
    )

    assert result.incident_reuse_rate == 0.0


@patch(
    "app.services.correlation_analytics_service."
    "CorrelationAnalyticsRepository.get_recent"
)
@patch(
    "app.services.correlation_analytics_service."
    "CorrelationAnalyticsRepository.count_by_column"
)
@patch(
    "app.services.correlation_analytics_service."
    "CorrelationAnalyticsRepository.get_totals"
)
def test_get_summary_maps_recent_correlations(
    totals_mock,
    counts_mock,
    recent_mock,
) -> None:
    """Expose compact recent decision records."""

    from app.core.correlation import (
        CorrelationApplicationStatus,
        CorrelationOutcome,
        CorrelationSignalFamily,
    )

    totals_mock.return_value = {
        "total_evaluations": 1,
        "applied_decisions": 1,
        "failed_decisions": 0,
        "pending_decisions": 0,
        "incidents_created": 0,
        "existing_incidents_matched": 1,
        "no_action_decisions": 0,
        "average_score": 0.9,
    }

    counts_mock.return_value = []

    recent_mock.return_value = [
        SimpleNamespace(
            id=91,
            source_alert_id=301,
            target_incident_id=21,
            outcome=(
                CorrelationOutcome
                .MATCHED_EXISTING
            ),
            application_status=(
                CorrelationApplicationStatus
                .APPLIED
            ),
            signal_family=(
                CorrelationSignalFamily
                .CONNECTIVITY
            ),
            score=Decimal("0.9000"),
            evaluated_at=NOW,
        )
    ]

    result = (
        CorrelationAnalyticsService
        .get_summary(
            db=SimpleNamespace(),
        )
    )

    item = result.recent_correlations[0]

    assert item.correlation_id == 91
    assert item.source_alert_id == 301
    assert item.target_incident_id == 21
    assert item.score == 0.9