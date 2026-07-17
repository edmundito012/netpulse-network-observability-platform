"""API tests for Incident Timeline operations."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import (
    Mock,
    patch,
)

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.main import app
from app.models.incident_timeline_event import (
    IncidentTimelineActorType,
    IncidentTimelineEventType,
)
from app.models.user import UserRole
from app.schemas.incident_timeline import (
    IncidentTimelinePaginationResponse,
    IncidentTimelineSummary,
)
from app.services.incident_exceptions import (
    IncidentNotFoundError,
)


NOW = datetime(
    2026,
    7,
    17,
    12,
    0,
    tzinfo=UTC,
)


client = TestClient(app)


def build_user(
    *,
    role: UserRole = UserRole.ADMIN,
):
    """Build an authenticated API user."""

    return SimpleNamespace(
        id=3,
        email="noc.operator@netpulse.test",
        username="noc-operator",
        role=role,
        is_active=True,
    )


def override_admin_user():
    """Return an authenticated administrator."""

    return build_user(
        role=UserRole.ADMIN,
    )


def build_event(
    *,
    event_type: IncidentTimelineEventType = (
        IncidentTimelineEventType
        .INCIDENT_CREATED
    ),
):
    """Build a complete timeline event response double."""

    return SimpleNamespace(
        id=11,
        incident_id=7,
        event_type=event_type,
        actor_type=(
            IncidentTimelineActorType.USER
        ),
        actor_id=3,
        actor_label="noc-operator",
        message="Incident timeline event",
        previous_value=None,
        new_value={
            "status": "OPEN",
        },
        event_metadata={
            "source": "api-test",
        },
        occurred_at=NOW,
    )


@pytest.fixture(autouse=True)
def authenticated_timeline_api():
    """Isolate FastAPI authentication overrides."""

    app.dependency_overrides[
        get_current_user
    ] = override_admin_user

    yield

    app.dependency_overrides.pop(
        get_current_user,
        None,
    )


@patch(
    "app.api.incident_timeline."
    "IncidentTimelineService.list_events"
)
def test_list_incident_timeline(
    list_events_mock: Mock,
) -> None:
    list_events_mock.return_value = (
        IncidentTimelinePaginationResponse(
            items=[
                build_event(),
            ],
            total_count=1,
            page=1,
            page_size=50,
            total_pages=1,
        )
    )

    response = client.get(
        "/incidents/"
        "INC-2026-000007/"
        "timeline"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["total_count"] == 1
    assert len(payload["items"]) == 1

    assert (
        payload["items"][0]["event_type"]
        == "INCIDENT_CREATED"
    )

    list_events_mock.assert_called_once_with(
        db=list_events_mock.call_args.kwargs[
            "db"
        ],
        public_id="INC-2026-000007",
        event_type=None,
        actor_type=None,
        page=1,
        page_size=50,
        newest_first=False,
    )


@patch(
    "app.api.incident_timeline."
    "IncidentTimelineService.list_events"
)
def test_list_timeline_supports_filters(
    list_events_mock: Mock,
) -> None:
    list_events_mock.return_value = (
        IncidentTimelinePaginationResponse(
            items=[],
            total_count=0,
            page=2,
            page_size=25,
            total_pages=0,
        )
    )

    response = client.get(
        "/incidents/"
        "INC-2026-000007/"
        "timeline"
        "?event_type=STATUS_CHANGED"
        "&actor_type=USER"
        "&page=2"
        "&page_size=25"
        "&newest_first=true"
    )

    assert response.status_code == 200

    call = list_events_mock.call_args.kwargs

    assert (
        call["event_type"]
        == IncidentTimelineEventType
        .STATUS_CHANGED
    )

    assert (
        call["actor_type"]
        == IncidentTimelineActorType.USER
    )

    assert call["page"] == 2
    assert call["page_size"] == 25
    assert call["newest_first"] is True


@patch(
    "app.api.incident_timeline."
    "IncidentTimelineService.get_summary"
)
def test_get_timeline_summary(
    get_summary_mock: Mock,
) -> None:
    get_summary_mock.return_value = (
        IncidentTimelineSummary(
            incident_id=7,
            public_id="INC-2026-000007",
            event_count=4,
            first_event_at=NOW,
            latest_event_at=NOW,
            last_event_type=(
                IncidentTimelineEventType
                .STATUS_CHANGED
            ),
        )
    )

    response = client.get(
        "/incidents/"
        "INC-2026-000007/"
        "timeline/summary"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["incident_id"] == 7
    assert payload["event_count"] == 4

    assert (
        payload["last_event_type"]
        == "STATUS_CHANGED"
    )


@patch(
    "app.api.incident_timeline."
    "IncidentTimelineService.get_latest_event"
)
def test_get_latest_timeline_event(
    get_latest_mock: Mock,
) -> None:
    get_latest_mock.return_value = (
        build_event(
            event_type=(
                IncidentTimelineEventType
                .COMMENT_ADDED
            )
        )
    )

    response = client.get(
        "/incidents/"
        "INC-2026-000007/"
        "timeline/latest"
    )

    assert response.status_code == 200

    assert (
        response.json()["event_type"]
        == "COMMENT_ADDED"
    )


@patch(
    "app.api.incident_timeline."
    "IncidentTimelineService.get_latest_event"
)
def test_latest_timeline_event_can_be_empty(
    get_latest_mock: Mock,
) -> None:
    get_latest_mock.return_value = None

    response = client.get(
        "/incidents/"
        "INC-2026-000007/"
        "timeline/latest"
    )

    assert response.status_code == 200
    assert response.json() is None


@patch(
    "app.api.incident_timeline."
    "IncidentTimelineService.add_comment"
)
@patch(
    "app.api.incident_timeline."
    "IncidentService.get_required_by_public_id"
)
def test_add_comment_uses_authenticated_actor(
    get_incident_mock: Mock,
    add_comment_mock: Mock,
) -> None:
    incident = SimpleNamespace(
        id=7,
        public_id="INC-2026-000007",
    )

    get_incident_mock.return_value = incident

    event = build_event(
        event_type=(
            IncidentTimelineEventType
            .COMMENT_ADDED
        )
    )

    event.message = (
        "ISP escalation opened"
    )

    add_comment_mock.return_value = event

    response = client.post(
        "/incidents/"
        "INC-2026-000007/"
        "timeline/comments",
        json={
            "message": (
                "ISP escalation opened"
            ),
            "metadata": {
                "ticket": "ISP-4821",
            },
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["event_type"] == (
        "COMMENT_ADDED"
    )

    assert payload["actor_id"] == 3
    assert payload["actor_label"] == (
        "noc-operator"
    )

    call = add_comment_mock.call_args.kwargs

    assert call["incident"] is incident
    assert call["actor_id"] == 3

    assert call["actor_label"] == (
        "noc-operator"
    )

    assert (
        call["comment_data"].metadata
        == {
            "ticket": "ISP-4821",
        }
    )


def test_viewer_can_read_timeline() -> None:
    """Viewer access remains read-only."""

    def override_viewer_user():
        return build_user(
            role=UserRole.VIEWER,
        )

    app.dependency_overrides[
        get_current_user
    ] = override_viewer_user

    with patch(
        "app.api.incident_timeline."
        "IncidentTimelineService.list_events"
    ) as list_events_mock:
        list_events_mock.return_value = (
            IncidentTimelinePaginationResponse(
                items=[],
                total_count=0,
                page=1,
                page_size=50,
                total_pages=0,
            )
        )

        response = client.get(
            "/incidents/"
            "INC-2026-000007/"
            "timeline"
        )

    assert response.status_code == 200


def test_viewer_cannot_add_comment() -> None:
    """Viewer users cannot mutate incident timelines."""

    def override_viewer_user():
        return build_user(
            role=UserRole.VIEWER,
        )

    app.dependency_overrides[
        get_current_user
    ] = override_viewer_user

    response = client.post(
        "/incidents/"
        "INC-2026-000007/"
        "timeline/comments",
        json={
            "message": (
                "Unauthorized comment"
            ),
        },
    )

    assert response.status_code == 403


def test_timeline_requires_authentication() -> None:
    """Unauthenticated callers cannot read timelines."""

    app.dependency_overrides.pop(
        get_current_user,
        None,
    )

    response = client.get(
        "/incidents/"
        "INC-2026-000007/"
        "timeline"
    )

    assert response.status_code in {
        401,
        403,
    }


@patch(
    "app.api.incident_timeline."
    "IncidentTimelineService.get_summary"
)
def test_missing_incident_returns_404(
    get_summary_mock: Mock,
) -> None:
    get_summary_mock.side_effect = (
        IncidentNotFoundError(
            "INC-2026-999999"
        )
    )

    response = client.get(
        "/incidents/"
        "INC-2026-999999/"
        "timeline/summary"
    )

    assert response.status_code == 404