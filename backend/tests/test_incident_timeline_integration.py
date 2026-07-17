"""Integration-style tests for automatic incident timeline recording."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.models.incident import (
    IncidentPriority,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)
from app.models.incident_timeline_event import (
    IncidentTimelineEventType,
)
from app.schemas.incident import (
    IncidentCreate,
    IncidentUpdate,
)
from app.services.incident_lifecycle_service import (
    IncidentLifecycleService,
)
from app.services.incident_service import (
    IncidentService,
)


def build_incident():
    """Build a complete incident service test double."""

    return SimpleNamespace(
        id=7,
        public_id="INC-2026-000007",
        title="WAN degradation",
        description="Initial description",
        status=IncidentStatus.OPEN,
        severity=IncidentSeverity.WARNING,
        priority=IncidentPriority.MEDIUM,
        source=IncidentSource.ALERT_ENGINE,
        owner_id=None,
        business_impact=None,
        root_cause=None,
        tags=[],
        incident_metadata={},
    )


@patch(
    "app.services.incident_service."
    "IncidentRepository.get_by_id"
)
@patch(
    "app.services.incident_service."
    "IncidentTimelineRecorderService."
    "record_incident_created"
)
@patch(
    "app.services.incident_service."
    "IncidentRepository.create"
)
def test_incident_creation_records_timeline_event(
    create_mock: Mock,
    record_mock: Mock,
    get_by_id_mock: Mock,
) -> None:
    incident = build_incident()

    create_mock.return_value = incident
    get_by_id_mock.return_value = incident

    result = IncidentService.create(
        db=Mock(),
        incident_data=IncidentCreate(
            title="WAN degradation",
            source=IncidentSource.ALERT_ENGINE,
        ),
    )

    assert result is incident

    record_mock.assert_called_once_with(
        db=create_mock.call_args.kwargs["db"],
        incident=incident,
    )


@patch(
    "app.services.incident_service."
    "IncidentTimelineRecorderService."
    "record_alert_attached"
)
@patch(
    "app.services.incident_service."
    "IncidentRepository.attach_alert"
)
@patch(
    "app.services.incident_service."
    "IncidentRepository.get_alert_link"
)
@patch(
    "app.services.incident_service."
    "AlertRepository.get_by_id"
)
def test_new_alert_attachment_records_event(
    get_alert_mock: Mock,
    get_link_mock: Mock,
    attach_mock: Mock,
    record_mock: Mock,
) -> None:
    db = Mock()
    incident = build_incident()

    get_alert_mock.return_value = (
        SimpleNamespace(id=42)
    )

    get_link_mock.return_value = None

    link = SimpleNamespace(
        incident_id=incident.id,
        alert_id=42,
    )

    attach_mock.return_value = link

    result = IncidentService.attach_alert(
        db=db,
        incident=incident,
        alert_id=42,
    )

    assert result is link

    record_mock.assert_called_once_with(
        db=db,
        incident=incident,
        alert_id=42,
        actor_type=record_mock.call_args.kwargs[
            "actor_type"
        ],
        actor_id=None,
        actor_label=None,
    )


@patch(
    "app.services.incident_service."
    "IncidentTimelineRecorderService."
    "record_alert_attached"
)
@patch(
    "app.services.incident_service."
    "IncidentRepository.get_alert_link"
)
@patch(
    "app.services.incident_service."
    "AlertRepository.get_by_id"
)
def test_idempotent_attachment_does_not_duplicate_event(
    get_alert_mock: Mock,
    get_link_mock: Mock,
    record_mock: Mock,
) -> None:
    incident = build_incident()

    existing_link = SimpleNamespace(
        incident_id=incident.id,
        alert_id=42,
    )

    get_alert_mock.return_value = (
        SimpleNamespace(id=42)
    )

    get_link_mock.return_value = (
        existing_link
    )

    result = IncidentService.attach_alert(
        db=Mock(),
        incident=incident,
        alert_id=42,
    )

    assert result is existing_link
    record_mock.assert_not_called()


@patch(
    "app.services.incident_lifecycle_service."
    "IncidentTimelineRecorderService."
    "record_status_changed"
)
@patch(
    "app.services.incident_lifecycle_service."
    "IncidentLifecycleRepository.transition"
)
def test_lifecycle_transition_records_status_change(
    transition_mock: Mock,
    record_mock: Mock,
) -> None:
    db = Mock()
    incident = build_incident()

    updated = build_incident()
    updated.status = (
        IncidentStatus.ACKNOWLEDGED
    )

    transition_mock.return_value = updated

    result = (
        IncidentLifecycleService
        .acknowledge(
            db=db,
            incident=incident,
        )
    )

    assert result is updated

    record_mock.assert_called_once()

    call = record_mock.call_args.kwargs

    assert (
        call["previous_status"]
        == IncidentStatus.OPEN
    )

    assert (
        call["new_status"]
        == IncidentStatus.ACKNOWLEDGED
    )


@patch(
    "app.services.incident_lifecycle_service."
    "IncidentTimelineRecorderService."
    "record_incident_resolved"
)
@patch(
    "app.services.incident_lifecycle_service."
    "IncidentLifecycleRepository.resolve"
)
def test_resolution_records_final_event(
    resolve_mock: Mock,
    record_mock: Mock,
) -> None:
    db = Mock()

    incident = build_incident()
    incident.status = IncidentStatus.MONITORING

    updated = build_incident()
    updated.status = IncidentStatus.RESOLVED

    resolve_mock.return_value = updated

    result = (
        IncidentLifecycleService.resolve(
            db=db,
            incident=incident,
            resolution_summary=(
                "WAN connectivity restored"
            ),
            root_cause=(
                "Upstream provider outage"
            ),
        )
    )

    assert result is updated

    record_mock.assert_called_once()

    call = record_mock.call_args.kwargs

    assert (
        call["previous_status"]
        == IncidentStatus.MONITORING
    )

    assert call["resolution_summary"] == (
        "WAN connectivity restored"
    )


@patch(
    "app.services.incident_service."
    "IncidentTimelineRecorderService."
    "record_severity_changed"
)
@patch(
    "app.services.incident_service."
    "IncidentRepository.update_details"
)
def test_severity_update_records_event(
    update_mock: Mock,
    record_mock: Mock,
) -> None:
    db = Mock()
    incident = build_incident()

    updated = build_incident()
    updated.severity = (
        IncidentSeverity.CRITICAL
    )

    update_mock.return_value = updated

    result = IncidentService.update(
        db=db,
        incident=incident,
        incident_data=IncidentUpdate(
            severity=(
                IncidentSeverity.CRITICAL
            )
        ),
    )

    assert result is updated

    record_mock.assert_called_once_with(
        db=db,
        incident=updated,
        previous_severity="WARNING",
        new_severity="CRITICAL",
        actor_type=record_mock.call_args.kwargs[
            "actor_type"
        ],
        actor_id=None,
        actor_label=None,
    )