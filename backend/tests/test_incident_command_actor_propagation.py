"""Tests for IncidentCommandService actor propagation."""

from types import SimpleNamespace
from unittest.mock import (
    Mock,
    patch,
)

from app.models.incident_timeline_event import (
    IncidentTimelineActorType,
)
from app.schemas.incident import (
    IncidentAlertAttachRequest,
    IncidentResolveRequest,
    IncidentUpdate,
)
from app.services.incident_actor_context import (
    IncidentActorContext,
)
from app.services.incident_command_service import (
    IncidentCommandService,
)


def build_actor() -> IncidentActorContext:
    """Build an authenticated operator context."""

    return IncidentActorContext.user(
        user_id=9,
        username="noc-operator",
    )


def build_incident():
    """Build a command-service incident double."""

    return SimpleNamespace(
        id=7,
        public_id="INC-2026-000007",
    )


@patch(
    "app.services.incident_command_service."
    "IncidentService.get_required_by_public_id"
)
@patch(
    "app.services.incident_command_service."
    "IncidentService.update"
)
def test_update_propagates_actor(
    update_mock: Mock,
    get_incident_mock: Mock,
) -> None:
    db = Mock()
    incident = build_incident()

    get_incident_mock.return_value = incident
    update_mock.return_value = incident

    actor = build_actor()

    IncidentCommandService.update(
        db=db,
        public_id=incident.public_id,
        incident_data=IncidentUpdate(
            title="Updated incident",
        ),
        actor=actor,
    )

    update_mock.assert_called_once_with(
        db=db,
        incident=incident,
        incident_data=update_mock
        .call_args
        .kwargs["incident_data"],
        actor_type=(
            IncidentTimelineActorType.USER
        ),
        actor_id=9,
        actor_label="noc-operator",
    )


@patch(
    "app.services.incident_command_service."
    "IncidentService.get_required_by_public_id"
)
@patch(
    "app.services.incident_command_service."
    "IncidentLifecycleService.acknowledge"
)
def test_acknowledge_propagates_actor(
    acknowledge_mock: Mock,
    get_incident_mock: Mock,
) -> None:
    db = Mock()
    incident = build_incident()

    get_incident_mock.return_value = incident
    acknowledge_mock.return_value = incident

    IncidentCommandService.acknowledge(
        db=db,
        public_id=incident.public_id,
        actor=build_actor(),
    )

    acknowledge_mock.assert_called_once_with(
        db=db,
        incident=incident,
        actor_type=(
            IncidentTimelineActorType.USER
        ),
        actor_id=9,
        actor_label="noc-operator",
    )


@patch(
    "app.services.incident_command_service."
    "IncidentService.get_required_by_public_id"
)
@patch(
    "app.services.incident_command_service."
    "IncidentLifecycleService.resolve"
)
def test_resolve_propagates_actor(
    resolve_mock: Mock,
    get_incident_mock: Mock,
) -> None:
    db = Mock()
    incident = build_incident()

    get_incident_mock.return_value = incident
    resolve_mock.return_value = incident

    IncidentCommandService.resolve(
        db=db,
        public_id=incident.public_id,
        resolution_data=(
            IncidentResolveRequest(
                resolution_summary=(
                    "Connectivity restored"
                ),
            )
        ),
        actor=build_actor(),
    )

    resolve_mock.assert_called_once_with(
        db=db,
        incident=incident,
        resolution_summary=(
            "Connectivity restored"
        ),
        root_cause=None,
        actor_type=(
            IncidentTimelineActorType.USER
        ),
        actor_id=9,
        actor_label="noc-operator",
    )


@patch(
    "app.services.incident_command_service."
    "IncidentService.get_required_by_public_id"
)
@patch(
    "app.services.incident_command_service."
    "IncidentService.attach_alert"
)
def test_attach_alerts_propagates_actor(
    attach_mock: Mock,
    get_incident_mock: Mock,
) -> None:
    db = Mock()
    incident = build_incident()

    get_incident_mock.return_value = incident

    IncidentCommandService.attach_alerts(
        db=db,
        public_id=incident.public_id,
        attachment_data=(
            IncidentAlertAttachRequest(
                alert_ids=[
                    42,
                    43,
                ]
            )
        ),
        actor=build_actor(),
    )

    assert attach_mock.call_count == 2

    for call in attach_mock.call_args_list:
        assert call.kwargs["actor_type"] == (
            IncidentTimelineActorType.USER
        )
        assert call.kwargs["actor_id"] == 9
        assert (
            call.kwargs["actor_label"]
            == "noc-operator"
        )