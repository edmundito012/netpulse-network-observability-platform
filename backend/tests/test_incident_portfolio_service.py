"""Tests for IncidentPortfolioService."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.models.incident import (
    IncidentPriority,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)
from app.services.incident_portfolio_service import (
    IncidentPortfolioService,
)


NOW = datetime(
    2026,
    7,
    16,
    12,
    0,
    tzinfo=UTC,
)


def build_incident():
    """Build a recent incident test double."""

    return SimpleNamespace(
        public_id="INC-2026-000001",
        title="WAN packet loss burst",
        status=IncidentStatus.INVESTIGATING,
        severity=IncidentSeverity.CRITICAL,
        priority=IncidentPriority.CRITICAL,
        source=IncidentSource.ALERT_ENGINE,
        started_at=(
            NOW
            - timedelta(minutes=10)
        ),
        detected_at=(
            NOW
            - timedelta(minutes=9)
        ),
        resolved_at=None,
        alert_links=[
            SimpleNamespace(),
            SimpleNamespace(),
        ],
    )


@patch(
    "app.services.incident_portfolio_service."
    "IncidentPortfolioRepository.get_latest"
)
@patch(
    "app.services.incident_portfolio_service."
    "IncidentPortfolioRepository."
    "get_mean_resolution_seconds"
)
@patch(
    "app.services.incident_portfolio_service."
    "IncidentPortfolioRepository."
    "count_affected_devices"
)
@patch(
    "app.services.incident_portfolio_service."
    "IncidentPortfolioRepository."
    "count_correlated_alerts"
)
@patch(
    "app.services.incident_portfolio_service."
    "IncidentPortfolioRepository."
    "count_by_status"
)
@patch(
    "app.services.incident_portfolio_service."
    "IncidentPortfolioRepository."
    "count_active_critical"
)
@patch(
    "app.services.incident_portfolio_service."
    "IncidentPortfolioRepository."
    "count_active"
)
@patch(
    "app.services.incident_portfolio_service."
    "IncidentPortfolioRepository.count_all"
)
def test_summary_contains_operational_metrics(
    count_all_mock: Mock,
    count_active_mock: Mock,
    count_critical_mock: Mock,
    count_status_mock: Mock,
    count_alerts_mock: Mock,
    count_devices_mock: Mock,
    mean_resolution_mock: Mock,
    latest_mock: Mock,
) -> None:
    count_all_mock.return_value = 12
    count_active_mock.return_value = 4
    count_critical_mock.return_value = 2

    count_status_mock.side_effect = [
        1,
        1,
        1,
        1,
        8,
    ]

    count_alerts_mock.return_value = 9
    count_devices_mock.return_value = 3
    mean_resolution_mock.return_value = 1320.0

    latest_mock.return_value = [
        build_incident(),
    ]

    result = (
        IncidentPortfolioService
        .get_summary(
            db=Mock(),
            now=NOW,
        )
    )

    assert result.total_incidents == 12
    assert result.active_incidents == 4
    assert result.critical_incidents == 2

    assert result.correlated_alerts == 9
    assert result.affected_devices == 3

    assert (
        result.mean_resolution_seconds
        == 1320.0
    )

    assert len(
        result.latest_incidents
    ) == 1

    latest = result.latest_incidents[0]

    assert latest.public_id == (
        "INC-2026-000001"
    )
    assert latest.alert_count == 2
    assert latest.duration_seconds == 600.0