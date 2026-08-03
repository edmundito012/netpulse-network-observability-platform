"""API tests for Correlation Engine analytics."""

from datetime import (
    UTC,
    datetime,
)
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.main import app
from app.models.user import UserRole
from app.schemas.correlation_analytics import (
    CorrelationAnalyticsSummary,
)


client = TestClient(app)


def override_viewer_user():
    """Return an authenticated viewer."""

    return SimpleNamespace(
        id=1,
        email="analytics-viewer@netpulse.test",
        username="analytics-viewer",
        role=UserRole.VIEWER,
        is_active=True,
    )


@pytest.fixture(autouse=True)
def authenticated_user():
    """Authenticate each API test."""

    app.dependency_overrides[
        get_current_user
    ] = override_viewer_user

    yield

    app.dependency_overrides.pop(
        get_current_user,
        None,
    )


def build_summary() -> CorrelationAnalyticsSummary:
    """Build a valid analytics response."""

    now = datetime.now(UTC)

    return CorrelationAnalyticsSummary(
        window_hours=24,
        window_started_at=now,
        generated_at=now,
        total_evaluations=10,
        applied_decisions=8,
        failed_decisions=2,
        pending_decisions=0,
        incidents_created=3,
        existing_incidents_matched=5,
        no_action_decisions=2,
        successful_decisions=8,
        average_score=0.81,
        application_success_rate=80.0,
        incident_reuse_rate=62.5,
        estimated_incidents_avoided=5,
        outcomes=[],
        application_statuses=[],
        signal_families=[],
        recent_correlations=[],
    )


@patch(
    "app.api.correlation_analytics."
    "CorrelationAnalyticsService.get_summary"
)
def test_get_correlation_analytics(
    summary_mock,
) -> None:
    """Return correlation analytics to viewers."""

    summary_mock.return_value = build_summary()

    response = client.get(
        "/analytics/correlations",
        params={
            "window_hours": 48,
            "recent_limit": 10,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["total_evaluations"] == 10

    assert (
        payload["application_success_rate"]
        == 80.0
    )

    assert payload["incident_reuse_rate"] == 62.5

    summary_mock.assert_called_once()

    kwargs = summary_mock.call_args.kwargs

    assert kwargs["window_hours"] == 48
    assert kwargs["recent_limit"] == 10


def test_correlation_analytics_rejects_bad_window(
) -> None:
    """Validate analytics temporal windows."""

    response = client.get(
        "/analytics/correlations",
        params={
            "window_hours": 0,
        },
    )

    assert response.status_code == 422


def test_correlation_analytics_requires_auth(
) -> None:
    """Reject unauthenticated analytics requests."""

    app.dependency_overrides.pop(
        get_current_user,
        None,
    )

    response = client.get(
        "/analytics/correlations"
    )

    assert response.status_code in {
        401,
        403,
    }


def test_correlation_analytics_is_in_openapi(
) -> None:
    """Expose correlation analytics in OpenAPI."""

    assert (
        "/analytics/correlations"
        in app.openapi()["paths"]
    )