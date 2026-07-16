"""API tests for the Incident Operations portfolio."""

from datetime import UTC, datetime
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.incident import (
    IncidentPriority,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)
from app.schemas.incident_portfolio import (
    IncidentPortfolioItem,
    IncidentPortfolioSummary,
)


client = TestClient(app)


NOW = datetime(
    2026,
    7,
    16,
    12,
    0,
    tzinfo=UTC,
)


def test_incident_portfolio_page_is_available() -> None:
    response = client.get(
        "/portfolio/incidents"
    )

    assert response.status_code == 200
    assert (
        "Incident Operations"
        in response.text
    )
    assert (
        'data-dashboard-ready="false"'
        in response.text
    )
    assert (
        "/portfolio/incidents/data"
        in response.text
    )


@patch(
    "app.api.portfolio_incidents."
    "IncidentPortfolioService.get_summary"
)
def test_incident_portfolio_data_endpoint(
    summary_mock,
) -> None:
    summary_mock.return_value = (
        IncidentPortfolioSummary(
            total_incidents=5,
            active_incidents=2,
            critical_incidents=1,
            open_incidents=1,
            acknowledged_incidents=0,
            investigating_incidents=1,
            monitoring_incidents=0,
            resolved_incidents=3,
            correlated_alerts=4,
            affected_devices=2,
            mean_resolution_seconds=600.0,
            latest_incidents=[
                IncidentPortfolioItem(
                    public_id=(
                        "INC-2026-000005"
                    ),
                    title=(
                        "Packet loss burst"
                    ),
                    status=(
                        IncidentStatus
                        .INVESTIGATING
                    ),
                    severity=(
                        IncidentSeverity
                        .CRITICAL
                    ),
                    priority=(
                        IncidentPriority
                        .CRITICAL
                    ),
                    source=(
                        IncidentSource
                        .ALERT_ENGINE
                    ),
                    alert_count=2,
                    started_at=NOW,
                    detected_at=NOW,
                    duration_seconds=120.0,
                )
            ],
        )
    )

    response = client.get(
        "/portfolio/incidents/data"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["total_incidents"] == 5
    assert payload["active_incidents"] == 2
    assert payload["critical_incidents"] == 1
    assert payload["correlated_alerts"] == 4

    assert (
        payload["latest_incidents"][0]
        ["public_id"]
        == "INC-2026-000005"
    )