"""Unit tests for IncidentTimelineRecorderService."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.models.incident import (
    IncidentPriority,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)
from app.models.incident_timeline_event import (
    IncidentTimelineActorType,
    IncidentTimelineEventType,
)
from app.services.incident_timeline_recorder_service import (
    IncidentTimelineRecorderService,
)


def build_incident(
    *,
    source: IncidentSource = (
        IncidentSource.ALERT_ENGINE
    ),
):
    """Build an incident used by recorder tests."""

    return SimpleNamespace(
        id=7,
        public_id="INC-2026-000007",
        title="Packet loss burst",
        status=IncidentStatus.OPEN,
        severity=IncidentSeverity.CRITICAL,
        priority=IncidentPriority.CRITICAL,
        source=source,
        owner_id=None,
    )


@patch(
    "app.services.incident_timeline_recorder_service."
    "IncidentTimelineRepository.append"
)
def test_created_event_maps_automation_source(
    append_mock: Mock,
) -> None:
    db = Mock()
    incident = build_incident()

    append_mock.return_value = (
        SimpleNamespace(id=1)
    )

    (
        IncidentTimelineRecorderService
        .record_incident_created(
            db=db,
            incident=incident,
        )
    )

    append_mock.assert_called_once_with(
        db=db,
        incident_id=7,
        event_type=(
            IncidentTimelineEventType
            .INCIDENT_CREATED
        ),
        actor_type=(
            IncidentTimelineActorType
            .AUTOMATION
        ),
        actor_id=None,
        actor_label=(
            "NetPulse ALERT_ENGINE"
        ),
        message=(
            "Incident INC-2026-000007 created"
        ),
        previous_value=None,
        new_value={
            "public_id": "INC-2026-000007",
            "title": "Packet loss burst",
            "status": "OPEN",
            "severity": "CRITICAL",
            "priority": "CRITICAL",
            "source": "ALERT_ENGINE",
            "owner_id": None,
        },
        event_metadata={
            "source": "ALERT_ENGINE",
        },
    )


@patch(
    "app.services.incident_timeline_recorder_service."
    "IncidentTimelineRepository.append"
)
def test_status_change_records_previous_and_new_values(
    append_mock: Mock,
) -> None:
    incident = build_incident()

    (
        IncidentTimelineRecorderService
        .record_status_changed(
            db=Mock(),
            incident=incident,
            previous_status=(
                IncidentStatus.OPEN
            ),
            new_status=(
                IncidentStatus.ACKNOWLEDGED
            ),
        )
    )

    call = append_mock.call_args.kwargs

    assert (
        call["event_type"]
        == IncidentTimelineEventType
        .STATUS_CHANGED
    )

    assert call["previous_value"] == {
        "status": "OPEN",
    }

    assert call["new_value"] == {
        "status": "ACKNOWLEDGED",
    }


@patch(
    "app.services.incident_timeline_recorder_service."
    "IncidentTimelineRepository.append"
)
def test_alert_attachment_records_alert_id(
    append_mock: Mock,
) -> None:
    incident = build_incident()

    (
        IncidentTimelineRecorderService
        .record_alert_attached(
            db=Mock(),
            incident=incident,
            alert_id=42,
        )
    )

    call = append_mock.call_args.kwargs

    assert (
        call["event_type"]
        == IncidentTimelineEventType
        .ALERT_ATTACHED
    )

    assert call["new_value"] == {
        "alert_id": 42,
    }