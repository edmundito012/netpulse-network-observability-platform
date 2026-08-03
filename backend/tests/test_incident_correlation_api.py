"""API tests for the Correlation Engine."""

from datetime import (
    UTC,
    datetime,
)
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.core.correlation import (
    CorrelationApplicationStatus,
    CorrelationOutcome,
    CorrelationReason,
    CorrelationSignalFamily,
)
from app.main import app
from app.models.user import UserRole
from app.schemas.incident_correlation import (
    CorrelationCandidateRead,
    CorrelationEvaluationResult,
)
from app.schemas.incident_correlation_application import (
    CorrelationApplicationResult,
)
from app.services.incident_correlation_query_service import (
    IncidentCorrelationNotFoundError,
)
from app.services.incident_correlation_service import (
    SourceAlertNotFoundError,
)


NOW = datetime(
    2026,
    7,
    21,
    18,
    0,
    tzinfo=UTC,
)


client = TestClient(app)


def override_admin_user():
    """Return an authenticated administrator."""

    return SimpleNamespace(
        id=1,
        email=(
            "correlation-admin@netpulse.test"
        ),
        username="correlation-admin",
        role=UserRole.ADMIN,
        is_active=True,
    )


def override_viewer_user():
    """Return an authenticated read-only user."""

    return SimpleNamespace(
        id=2,
        email=(
            "correlation-viewer@netpulse.test"
        ),
        username="correlation-viewer",
        role=UserRole.VIEWER,
        is_active=True,
    )


@pytest.fixture(autouse=True)
def authenticated_correlation_api():
    """Apply authentication only during each test."""

    app.dependency_overrides[
        get_current_user
    ] = override_admin_user

    yield

    app.dependency_overrides.pop(
        get_current_user,
        None,
    )


def build_evaluation() -> (
    CorrelationEvaluationResult
):
    """Build a complete evaluation response."""

    return CorrelationEvaluationResult(
        source_alert_id=101,
        outcome=(
            CorrelationOutcome.MATCHED_EXISTING
        ),
        signal_family=(
            CorrelationSignalFamily.CONNECTIVITY
        ),
        score=0.90,
        threshold=0.65,
        correlated=True,
        target_incident_id=15,
        target_incident_public_id=(
            "INC-2026-000015"
        ),
        reasons=[
            CorrelationReason.SAME_DEVICE,
            CorrelationReason
            .WITHIN_TEMPORAL_WINDOW,
            CorrelationReason
            .COMPATIBLE_SIGNAL_FAMILY,
        ],
        candidate_count=1,
        window_seconds=900,
        explanation=(
            "Alert matched an active incident."
        ),
        candidates=[
            CorrelationCandidateRead(
                incident_id=15,
                public_id=(
                    "INC-2026-000015"
                ),
                score=0.90,
                reasons=[
                    CorrelationReason
                    .SAME_DEVICE,
                ],
                time_distance_seconds=30.0,
                is_active=True,
            ),
        ],
    )


def build_correlation(
    *,
    correlation_id: int = 44,
    application_status: (
        CorrelationApplicationStatus
    ) = (
        CorrelationApplicationStatus
        .EVALUATED
    ),
):
    """Build a persisted correlation test double."""

    return SimpleNamespace(
        id=correlation_id,
        correlation_key=(
            "correlation:v1:alert:101:test"
        ),
        source_alert_id=101,
        target_incident_id=15,
        outcome=(
            CorrelationOutcome.MATCHED_EXISTING
        ),
        application_status=(
            application_status
        ),
        signal_family=(
            CorrelationSignalFamily.CONNECTIVITY
        ),
        score=Decimal("0.9000"),
        threshold=Decimal("0.6500"),
        reasons=[
            CorrelationReason.SAME_DEVICE.value,
            CorrelationReason
            .WITHIN_TEMPORAL_WINDOW
            .value,
        ],
        candidate_count=1,
        window_seconds=900,
        explanation=(
            "Alert matched an active incident."
        ),
        correlation_metadata={
            "engine": (
                "deterministic-correlation-v1"
            ),
        },
        failure_reason=None,
        evaluated_at=NOW,
        applied_at=(
            NOW
            if (
                application_status
                == CorrelationApplicationStatus
                .APPLIED
            )
            else None
        ),
    )


@patch(
    "app.api.incident_correlations."
    "IncidentCorrelationService."
    "evaluate_and_persist"
)
def test_evaluate_correlation_endpoint(
    evaluate_mock,
) -> None:
    """Evaluate and persist an alert correlation."""

    evaluate_mock.return_value = (
        build_evaluation(),
        build_correlation(),
        True,
    )

    response = client.post(
        "/incident-correlations/"
        "evaluate/101",
        json={},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["correlation_id"] == 44
    assert payload["persistence_created"] is True

    assert payload["source_alert_id"] == 101

    assert payload["outcome"] == (
        "MATCHED_EXISTING"
    )

    assert payload["score"] == 0.90

    assert payload["target_incident_id"] == 15

    evaluate_mock.assert_called_once()

    configuration = (
        evaluate_mock.call_args.kwargs[
            "configuration"
        ]
    )

    assert configuration.window_seconds == 900
    assert configuration.threshold == 0.65
    assert configuration.max_candidates == 25


@patch(
    "app.api.incident_correlations."
    "IncidentCorrelationService."
    "evaluate_and_persist"
)
def test_evaluate_accepts_custom_configuration(
    evaluate_mock,
) -> None:
    """Pass validated runtime options to the service."""

    evaluate_mock.return_value = (
        build_evaluation(),
        build_correlation(),
        True,
    )

    response = client.post(
        "/incident-correlations/"
        "evaluate/101",
        json={
            "window_seconds": 1800,
            "threshold": 0.75,
            "max_candidates": 50,
        },
    )

    assert response.status_code == 200

    configuration = (
        evaluate_mock.call_args.kwargs[
            "configuration"
        ]
    )

    assert configuration.window_seconds == 1800
    assert configuration.threshold == 0.75
    assert configuration.max_candidates == 50


@patch(
    "app.api.incident_correlations."
    "IncidentCorrelationApplicationService."
    "evaluate_and_apply"
)
def test_apply_correlation_endpoint(
    apply_mock,
) -> None:
    """Evaluate and apply a correlation decision."""

    apply_mock.return_value = (
        CorrelationApplicationResult(
            correlation_id=44,
            source_alert_id=101,
            outcome=(
                CorrelationOutcome
                .MATCHED_EXISTING
            ),
            application_status=(
                CorrelationApplicationStatus
                .APPLIED
            ),
            incident_id=15,
            incident_public_id=(
                "INC-2026-000015"
            ),
            incident_created=False,
            alert_attached=True,
            replayed=False,
        )
    )

    response = client.post(
        "/incident-correlations/apply/101",
        json={},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["correlation_id"] == 44

    assert payload["application_status"] == (
        "APPLIED"
    )

    assert payload["incident_id"] == 15
    assert payload["alert_attached"] is True
    assert payload["incident_created"] is False
    assert payload["replayed"] is False


@patch(
    "app.api.incident_correlations."
    "IncidentCorrelationApplicationService."
    "evaluate_and_apply"
)
def test_apply_endpoint_returns_replayed_result(
    apply_mock,
) -> None:
    """Expose idempotent application replays."""

    apply_mock.return_value = (
        CorrelationApplicationResult(
            correlation_id=44,
            source_alert_id=101,
            outcome=(
                CorrelationOutcome.CREATE_NEW
            ),
            application_status=(
                CorrelationApplicationStatus
                .APPLIED
            ),
            incident_id=20,
            incident_public_id=(
                "INC-2026-000020"
            ),
            incident_created=True,
            alert_attached=False,
            replayed=True,
        )
    )

    response = client.post(
        "/incident-correlations/apply/101",
        json={},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["incident_created"] is True
    assert payload["alert_attached"] is False
    assert payload["replayed"] is True


@patch(
    "app.api.incident_correlations."
    "IncidentCorrelationQueryService."
    "get_required"
)
def test_get_correlation_endpoint(
    get_mock,
) -> None:
    """Retrieve one persisted correlation."""

    get_mock.return_value = build_correlation()

    response = client.get(
        "/incident-correlations/44"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["id"] == 44
    assert payload["source_alert_id"] == 101

    assert payload["outcome"] == (
        "MATCHED_EXISTING"
    )

    assert payload["metadata"] == {
        "engine": (
            "deterministic-correlation-v1"
        ),
    }


@patch(
    "app.api.incident_correlations."
    "IncidentCorrelationQueryService."
    "get_required"
)
def test_get_unknown_correlation_returns_404(
    get_mock,
) -> None:
    """Return HTTP 404 for unknown correlation IDs."""

    get_mock.side_effect = (
        IncidentCorrelationNotFoundError(
            999_999
        )
    )

    response = client.get(
        "/incident-correlations/999999"
    )

    assert response.status_code == 404

    assert "was not found" in (
        response.json()["detail"]
    )


@patch(
    "app.api.incident_correlations."
    "IncidentCorrelationQueryService."
    "list_correlations"
)
def test_list_correlations_endpoint(
    list_mock,
) -> None:
    """Return paginated correlation history."""

    list_mock.return_value = {
        "items": [
            build_correlation(),
        ],
        "total_count": 1,
        "page": 1,
        "page_size": 20,
        "total_pages": 1,
    }

    response = client.get(
        "/incident-correlations"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["total_count"] == 1
    assert payload["page"] == 1
    assert len(payload["items"]) == 1


@patch(
    "app.api.incident_correlations."
    "IncidentCorrelationQueryService."
    "list_correlations"
)
def test_list_correlations_passes_filters(
    list_mock,
) -> None:
    """Pass API filters into the query service."""

    list_mock.return_value = {
        "items": [],
        "total_count": 0,
        "page": 2,
        "page_size": 10,
        "total_pages": 0,
    }

    response = client.get(
        "/incident-correlations",
        params={
            "source_alert_id": 101,
            "target_incident_id": 15,
            "outcome": (
                "MATCHED_EXISTING"
            ),
            "application_status": (
                "APPLIED"
            ),
            "signal_family": (
                "CONNECTIVITY"
            ),
            "page": 2,
            "page_size": 10,
        },
    )

    assert response.status_code == 200

    kwargs = (
        list_mock.call_args.kwargs
    )

    assert kwargs["source_alert_id"] == 101
    assert kwargs["target_incident_id"] == 15

    assert kwargs["outcome"] == (
        CorrelationOutcome.MATCHED_EXISTING
    )

    assert kwargs["application_status"] == (
        CorrelationApplicationStatus.APPLIED
    )

    assert kwargs["signal_family"] == (
        CorrelationSignalFamily.CONNECTIVITY
    )

    assert kwargs["page"] == 2
    assert kwargs["page_size"] == 10


@patch(
    "app.api.incident_correlations."
    "IncidentCorrelationService."
    "evaluate_and_persist"
)
def test_missing_source_alert_returns_404(
    evaluate_mock,
) -> None:
    """Translate a missing source alert into HTTP 404."""

    evaluate_mock.side_effect = (
        SourceAlertNotFoundError(
            "source alert 999 was not found"
        )
    )

    response = client.post(
        "/incident-correlations/"
        "evaluate/999",
        json={},
    )

    assert response.status_code == 404
    assert "was not found" in (
        response.json()["detail"]
    )


def test_invalid_execution_options_return_422() -> None:
    """Reject unsafe correlation configuration."""

    response = client.post(
        "/incident-correlations/"
        "evaluate/101",
        json={
            "window_seconds": 30,
            "threshold": 1.5,
            "max_candidates": 0,
        },
    )

    assert response.status_code == 422


def test_correlation_endpoints_require_authentication() -> None:
    """Reject unauthenticated correlation requests."""

    app.dependency_overrides.pop(
        get_current_user,
        None,
    )

    response = client.get(
        "/incident-correlations"
    )

    assert response.status_code in {
        401,
        403,
    }


def test_viewer_can_read_correlations() -> None:
    """Allow viewers to read correlation history."""

    app.dependency_overrides[
        get_current_user
    ] = override_viewer_user

    with patch(
        "app.api.incident_correlations."
        "IncidentCorrelationQueryService."
        "list_correlations"
    ) as list_mock:
        list_mock.return_value = {
            "items": [],
            "total_count": 0,
            "page": 1,
            "page_size": 20,
            "total_pages": 0,
        }

        response = client.get(
            "/incident-correlations"
        )

    assert response.status_code == 200


def test_viewer_cannot_evaluate_correlations() -> None:
    """Keep correlation persistence restricted to operators."""

    app.dependency_overrides[
        get_current_user
    ] = override_viewer_user

    response = client.post(
        "/incident-correlations/"
        "evaluate/101",
        json={},
    )

    assert response.status_code == 403


def test_viewer_cannot_apply_correlations() -> None:
    """Keep decision application restricted to operators."""

    app.dependency_overrides[
        get_current_user
    ] = override_viewer_user

    response = client.post(
        "/incident-correlations/apply/101",
        json={},
    )

    assert response.status_code == 403


def test_correlation_routes_exist_in_openapi() -> None:
    """Expose all Correlation Engine routes in OpenAPI."""

    openapi = app.openapi()

    paths = openapi["paths"]

    assert (
        "/incident-correlations/"
        "evaluate/{alert_id}"
        in paths
    )

    assert (
        "/incident-correlations/"
        "apply/{alert_id}"
        in paths
    )

    assert "/incident-correlations" in paths

    assert (
        "/incident-correlations/"
        "{correlation_id}"
        in paths
    )