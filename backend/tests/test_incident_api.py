"""API tests for Incident Engine operations."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.main import app
from app.models.incident import (
    IncidentPriority,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)
from app.models.user import UserRole
from app.services.incident_exceptions import (
    IncidentNotFoundError,
)
from app.services.incident_service import (
    IncidentStatistics,
)


NOW = datetime(
    2026,
    7,
    16,
    12,
    0,
    tzinfo=UTC,
)


client = TestClient(app)


def build_incident(
    *,
    status: IncidentStatus = IncidentStatus.OPEN,
):
    """Build a complete API incident test double."""

    return SimpleNamespace(
        id=1,
        public_id="INC-2026-000001",
        title="WAN degradation",
        description="Madrid office affected",
        status=status,
        severity=IncidentSeverity.CRITICAL,
        priority=IncidentPriority.HIGH,
        source=IncidentSource.ALERT_ENGINE,
        owner_id=None,
        business_impact="Video calls degraded",
        root_cause=None,
        resolution_summary=None,
        tags=[
            "wan",
        ],
        incident_metadata={},
        started_at=NOW,
        detected_at=NOW,
        acknowledged_at=None,
        resolved_at=None,
        created_at=NOW,
        updated_at=NOW,
        alert_links=[],
    )


def override_admin_user():
    """Return an authenticated administrator."""

    return SimpleNamespace(
        id=1,
        email="incident-admin@netpulse.test",
        username="incident-admin",
        role=UserRole.ADMIN,
        is_active=True,
    )


@pytest.fixture(autouse=True)
def authenticated_incident_api():
    """Apply authentication only while each incident API test runs.

    Dependency overrides are global FastAPI application state. Removing
    the override after every test prevents this module from disabling
    authentication in unrelated test modules.
    """

    app.dependency_overrides[
        get_current_user
    ] = override_admin_user

    yield

    app.dependency_overrides.pop(
        get_current_user,
        None,
    )


@patch(
    "app.api.incidents."
    "IncidentCommandService.create"
)
def test_create_incident_endpoint(
    create_mock,
) -> None:
    create_mock.return_value = build_incident()

    response = client.post(
        "/incidents",
        json={
            "title": "WAN degradation",
            "severity": "CRITICAL",
            "priority": "HIGH",
            "source": "ALERT_ENGINE",
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["public_id"] == (
        "INC-2026-000001"
    )
    assert payload["status"] == "OPEN"
    assert payload["severity"] == "CRITICAL"


@patch(
    "app.api.incidents."
    "IncidentService.list_incidents"
)
def test_list_incidents_endpoint(
    list_mock,
) -> None:
    list_mock.return_value = {
        "items": [
            build_incident(),
        ],
        "total_count": 1,
        "page": 1,
        "page_size": 20,
        "total_pages": 1,
    }

    response = client.get(
        "/incidents",
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["total_count"] == 1
    assert len(payload["items"]) == 1


@patch(
    "app.api.incidents."
    "IncidentService.get_required_by_public_id"
)
def test_get_incident_endpoint(
    get_mock,
) -> None:
    get_mock.return_value = build_incident()

    response = client.get(
        "/incidents/INC-2026-000001",
    )

    assert response.status_code == 200
    assert response.json()["public_id"] == (
        "INC-2026-000001"
    )


@patch(
    "app.api.incidents."
    "IncidentService.get_required_by_public_id"
)
def test_get_incident_returns_404(
    get_mock,
) -> None:
    get_mock.side_effect = (
        IncidentNotFoundError(
            "INC-2026-999999"
        )
    )

    response = client.get(
        "/incidents/INC-2026-999999",
    )

    assert response.status_code == 404


@patch(
    "app.api.incidents."
    "IncidentCommandService.acknowledge"
)
def test_acknowledge_incident_endpoint(
    acknowledge_mock,
) -> None:
    acknowledge_mock.return_value = (
        build_incident(
            status=(
                IncidentStatus.ACKNOWLEDGED
            )
        )
    )

    response = client.post(
        "/incidents/"
        "INC-2026-000001/"
        "acknowledge"
    )

    assert response.status_code == 200
    assert (
        response.json()["status"]
        == "ACKNOWLEDGED"
    )


@patch(
    "app.api.incidents."
    "IncidentCommandService.resolve"
)
def test_resolve_incident_endpoint(
    resolve_mock,
) -> None:
    incident = build_incident(
        status=IncidentStatus.RESOLVED
    )

    incident.resolution_summary = (
        "Connectivity restored"
    )
    incident.root_cause = (
        "Upstream provider outage"
    )
    incident.resolved_at = NOW

    resolve_mock.return_value = incident

    response = client.post(
        "/incidents/"
        "INC-2026-000001/"
        "resolve",
        json={
            "resolution_summary": (
                "Connectivity restored"
            ),
            "root_cause": (
                "Upstream provider outage"
            ),
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == (
        "RESOLVED"
    )


@patch(
    "app.api.incidents."
    "IncidentCommandService.detach_alert"
)
def test_detach_alert_endpoint(
    detach_mock,
) -> None:
    response = client.delete(
        "/incidents/"
        "INC-2026-000001/"
        "alerts/7"
    )

    assert response.status_code == 200
    assert response.json() == {
        "public_id": "INC-2026-000001",
        "alert_id": 7,
        "detached": True,
    }

    detach_mock.assert_called_once()


@patch(
    "app.api.incidents."
    "IncidentService.get_statistics"
)
@patch(
    "app.api.incidents."
    "IncidentService.get_required_by_public_id"
)
def test_incident_statistics_endpoint(
    get_incident_mock,
    statistics_mock,
) -> None:
    get_incident_mock.return_value = (
        build_incident()
    )

    statistics_mock.return_value = (
        IncidentStatistics(
            incident_id=1,
            public_id=(
                "INC-2026-000001"
            ),
            alert_count=5,
            affected_device_count=2,
            duration_seconds=900.0,
            is_active=True,
        )
    )

    response = client.get(
        "/incidents/"
        "INC-2026-000001/"
        "statistics"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["alert_count"] == 5
    assert (
        payload["affected_device_count"]
        == 2
    )
    assert payload["duration_seconds"] == 900.0


def test_incidents_require_authentication() -> None:
    """Incident endpoints reject unauthenticated requests."""

    app.dependency_overrides.pop(
        get_current_user,
        None,
    )

    response = client.get(
        "/incidents",
    )

    assert response.status_code in {
        401,
        403,
    }


def test_viewer_cannot_create_incident() -> None:
    """Viewer access is read-only."""

    def override_viewer_user():
        return SimpleNamespace(
            id=2,
            email="incident-viewer@netpulse.test",
            username="incident-viewer",
            role=UserRole.VIEWER,
            is_active=True,
        )

    app.dependency_overrides[
        get_current_user
    ] = override_viewer_user

    response = client.post(
        "/incidents",
        json={
            "title": "Unauthorized incident",
        },
    )

    assert response.status_code == 403