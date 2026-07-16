"""Unit tests for incident lifecycle transitions."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from app.models.incident import IncidentStatus
from app.services.incident_exceptions import (
    IncidentResolutionError,
    InvalidIncidentTransitionError,
)
from app.services.incident_lifecycle_service import (
    IncidentLifecycleService,
)


def build_incident(
    status: IncidentStatus,
):
    """Create an in-memory incident test double."""

    return SimpleNamespace(
        id=1,
        public_id="INC-2026-000001",
        status=status,
        acknowledged_at=None,
        resolved_at=None,
        root_cause=None,
        resolution_summary=None,
        updated_at=datetime.now(UTC),
    )


@patch(
    "app.services.incident_lifecycle_service."
    "IncidentLifecycleRepository.transition"
)
def test_open_incident_can_be_acknowledged(
    transition_mock: Mock,
) -> None:
    db = Mock()

    incident = build_incident(
        IncidentStatus.OPEN
    )

    transition_mock.return_value = incident

    result = (
        IncidentLifecycleService.acknowledge(
            db=db,
            incident=incident,
        )
    )

    assert result is incident

    transition_mock.assert_called_once_with(
        db=db,
        incident=incident,
        target_status=(
            IncidentStatus.ACKNOWLEDGED
        ),
    )


@patch(
    "app.services.incident_lifecycle_service."
    "IncidentLifecycleRepository.transition"
)
def test_open_incident_can_start_investigation(
    transition_mock: Mock,
) -> None:
    db = Mock()

    incident = build_incident(
        IncidentStatus.OPEN
    )

    transition_mock.return_value = incident

    IncidentLifecycleService.start_investigation(
        db=db,
        incident=incident,
    )

    transition_mock.assert_called_once_with(
        db=db,
        incident=incident,
        target_status=(
            IncidentStatus.INVESTIGATING
        ),
    )


@patch(
    "app.services.incident_lifecycle_service."
    "IncidentLifecycleRepository.transition"
)
def test_investigating_incident_can_start_monitoring(
    transition_mock: Mock,
) -> None:
    db = Mock()

    incident = build_incident(
        IncidentStatus.INVESTIGATING
    )

    transition_mock.return_value = incident

    IncidentLifecycleService.start_monitoring(
        db=db,
        incident=incident,
    )

    transition_mock.assert_called_once_with(
        db=db,
        incident=incident,
        target_status=IncidentStatus.MONITORING,
    )


@patch(
    "app.services.incident_lifecycle_service."
    "IncidentLifecycleRepository.resolve"
)
def test_monitored_incident_can_be_resolved(
    resolve_mock: Mock,
) -> None:
    db = Mock()

    incident = build_incident(
        IncidentStatus.MONITORING
    )

    resolve_mock.return_value = incident

    result = IncidentLifecycleService.resolve(
        db=db,
        incident=incident,
        resolution_summary=(
            "WAN provider restored connectivity"
        ),
        root_cause="Upstream provider outage",
    )

    assert result is incident

    resolve_mock.assert_called_once_with(
        db=db,
        incident=incident,
        resolution_summary=(
            "WAN provider restored connectivity"
        ),
        root_cause="Upstream provider outage",
    )


@pytest.mark.parametrize(
    ("current_status", "target_status"),
    [
        (
            IncidentStatus.OPEN,
            IncidentStatus.RESOLVED,
        ),
        (
            IncidentStatus.MONITORING,
            IncidentStatus.INVESTIGATING,
        ),
        (
            IncidentStatus.RESOLVED,
            IncidentStatus.OPEN,
        ),
        (
            IncidentStatus.ACKNOWLEDGED,
            IncidentStatus.MONITORING,
        ),
    ],
)
def test_invalid_transitions_are_rejected(
    current_status: IncidentStatus,
    target_status: IncidentStatus,
) -> None:
    incident = build_incident(
        current_status
    )

    with pytest.raises(
        InvalidIncidentTransitionError
    ):
        IncidentLifecycleService.transition(
            db=Mock(),
            incident=incident,
            target_status=target_status,
        )


def test_resolution_requires_summary() -> None:
    incident = build_incident(
        IncidentStatus.MONITORING
    )

    with pytest.raises(
        IncidentResolutionError
    ):
        IncidentLifecycleService.resolve(
            db=Mock(),
            incident=incident,
            resolution_summary="  ",
        )


def test_transition_to_same_status_is_idempotent() -> None:
    incident = build_incident(
        IncidentStatus.INVESTIGATING
    )

    result = (
        IncidentLifecycleService.transition(
            db=Mock(),
            incident=incident,
            target_status=(
                IncidentStatus.INVESTIGATING
            ),
        )
    )

    assert result is incident