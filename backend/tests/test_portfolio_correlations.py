"""Tests for the public Correlation Engine dashboard."""

from datetime import (
    UTC,
    datetime,
)
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.correlation_analytics import (
    CorrelationAnalyticsSummary,
)


client = TestClient(app)


def build_summary() -> CorrelationAnalyticsSummary:
    """Build a valid public dashboard response."""

    now = datetime.now(UTC)

    return CorrelationAnalyticsSummary(
        window_hours=168,
        window_started_at=now,
        generated_at=now,
        total_evaluations=12,
        applied_decisions=10,
        failed_decisions=2,
        pending_decisions=0,
        incidents_created=4,
        existing_incidents_matched=6,
        no_action_decisions=2,
        successful_decisions=10,
        average_score=0.82,
        application_success_rate=83.33,
        incident_reuse_rate=60.0,
        estimated_incidents_avoided=6,
        outcomes=[],
        application_statuses=[],
        signal_families=[],
        recent_correlations=[],
    )


def test_portfolio_correlation_dashboard_returns_html(
) -> None:
    """Render the public correlation dashboard."""

    response = client.get(
        "/portfolio/correlations"
    )

    assert response.status_code == 200

    assert (
        "text/html"
        in response.headers["content-type"]
    )

    assert (
        "Correlation Intelligence"
        in response.text
    )

    assert (
        "/portfolio/correlations/data"
        in response.text
    )


@patch(
    "app.api.portfolio_correlations."
    "CorrelationAnalyticsService.get_summary"
)
def test_portfolio_correlation_data(
    summary_mock,
) -> None:
    """Expose public correlation analytics data."""

    summary_mock.return_value = build_summary()

    response = client.get(
        "/portfolio/correlations/data",
        params={
            "window_hours": 168,
            "recent_limit": 20,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["total_evaluations"] == 12

    assert (
        payload["estimated_incidents_avoided"]
        == 6
    )

    kwargs = summary_mock.call_args.kwargs

    assert kwargs["window_hours"] == 168
    assert kwargs["recent_limit"] == 20


def test_portfolio_correlation_data_validates_window(
) -> None:
    """Reject invalid dashboard windows."""

    response = client.get(
        "/portfolio/correlations/data",
        params={
            "window_hours": 0,
        },
    )

    assert response.status_code == 422


def test_portfolio_correlation_routes_are_hidden_from_openapi(
) -> None:
    """Keep portfolio presentation routes out of API docs."""

    paths = app.openapi()["paths"]

    assert (
        "/portfolio/correlations"
        not in paths
    )

    assert (
        "/portfolio/correlations/data"
        not in paths
    )