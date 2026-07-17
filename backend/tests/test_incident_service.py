"""Unit tests for IncidentService application orchestration."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from app.models.incident import (
    IncidentPriority,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)
from app.schemas.incident import IncidentCreate
from app.services.incident_exceptions import (
    IncidentAlertConflictError,
    IncidentAlertNotAttachedError,
    IncidentAlertNotFoundError,
    IncidentNotFoundError,
    IncidentOwnerNotFoundError,
)
from app.services.incident_service import (
    IncidentService,
)
from app.models.incident_timeline_event import (
    IncidentTimelineActorType,
)

def build_incident():
    return SimpleNamespace(
        id=21,
        public_id="INC-2026-000021",
        title="WAN degradation",
        description=None,
        status=IncidentStatus.OPEN,
        severity=IncidentSeverity.CRITICAL,
        priority=IncidentPriority.HIGH,
        source=IncidentSource.ALERT_ENGINE,
        owner_id=None,
        business_impact=None,
        root_cause=None,
        tags=[],
        incident_metadata={},
        started_at=datetime(
            2026,
            7,
            16,
            10,
            0,
            tzinfo=UTC,
        ),
        resolved_at=None,
    )

    return SimpleNamespace(
        id=21,
        public_id="INC-2026-000021",
        title="WAN degradation",
        status=IncidentStatus.OPEN,
        started_at=started_at,
        resolved_at=None,
    )


@patch(
    "app.services.incident_service."
    "IncidentRepository.get_by_id"
)
@patch(
    "app.services.incident_service."
    "IncidentRepository.create"
)
@patch(
    "app.services.incident_service."
    "IncidentRepository.get_alert_link"
)
@patch(
    "app.services.incident_service."
    "AlertRepository.get_by_id"
)
def test_create_incident_validates_and_attaches_alerts(
    get_alert_mock: Mock,
    get_alert_link_mock: Mock,
    create_mock: Mock,
    get_incident_mock: Mock,
) -> None:
    db = Mock()
    incident = build_incident()

    get_alert_mock.return_value = SimpleNamespace(
        id=7,
    )
    get_alert_link_mock.return_value = None
    create_mock.return_value = incident
    get_incident_mock.return_value = incident

    payload = IncidentCreate(
        title="WAN degradation",
        severity=IncidentSeverity.CRITICAL,
        priority=IncidentPriority.HIGH,
        source=IncidentSource.ALERT_ENGINE,
        alert_ids=[
            7,
        ],
    )

    with patch.object(
        IncidentService,
        "attach_alert",
    ) as attach_mock:
        result = IncidentService.create(
            db=db,
            incident_data=payload,
        )

    assert result is incident

    create_mock.assert_called_once_with(
        db=db,
        title="WAN degradation",
        description=None,
        severity=IncidentSeverity.CRITICAL,
        priority=IncidentPriority.HIGH,
        source=IncidentSource.ALERT_ENGINE,
        owner_id=None,
        business_impact=None,
        started_at=None,
        tags=[],
        incident_metadata={},
    )

    attach_mock.assert_called_once_with(
        db=db,
        incident=incident,
        alert_id=7,
        actor_type=(
            IncidentTimelineActorType.AUTOMATION
        ),
        actor_label="NetPulse ALERT_ENGINE",
    )


@patch(
    "app.services.incident_service."
    "IncidentRepository.get_by_id"
)
def test_get_required_incident_raises_when_missing(
    get_by_id_mock: Mock,
) -> None:
    get_by_id_mock.return_value = None

    with pytest.raises(
        IncidentNotFoundError
    ):
        IncidentService.get_required_by_id(
            db=Mock(),
            incident_id=404,
        )


@patch(
    "app.services.incident_service."
    "UserRepository.get_by_id"
)
def test_assign_owner_rejects_unknown_user(
    get_user_mock: Mock,
) -> None:
    get_user_mock.return_value = None

    with pytest.raises(
        IncidentOwnerNotFoundError
    ):
        IncidentService.assign_owner(
            db=Mock(),
            incident=build_incident(),
            owner_id=999,
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
def test_attach_alert_is_idempotent(
    get_alert_mock: Mock,
    get_alert_link_mock: Mock,
    attach_alert_mock: Mock,
) -> None:
    incident = build_incident()

    get_alert_mock.return_value = SimpleNamespace(
        id=7,
    )

    existing_link = SimpleNamespace(
        incident_id=incident.id,
        alert_id=7,
        incident=incident,
    )

    get_alert_link_mock.return_value = (
        existing_link
    )

    result = IncidentService.attach_alert(
        db=Mock(),
        incident=incident,
        alert_id=7,
    )

    assert result is existing_link
    attach_alert_mock.assert_not_called()


@patch(
    "app.services.incident_service."
    "IncidentRepository.get_alert_link"
)
@patch(
    "app.services.incident_service."
    "AlertRepository.get_by_id"
)
def test_attach_alert_rejects_other_incident(
    get_alert_mock: Mock,
    get_alert_link_mock: Mock,
) -> None:
    get_alert_mock.return_value = SimpleNamespace(
        id=7,
    )

    get_alert_link_mock.return_value = (
        SimpleNamespace(
            incident_id=100,
            incident=SimpleNamespace(
                public_id="INC-2026-000100"
            ),
        )
    )

    with pytest.raises(
        IncidentAlertConflictError
    ):
        IncidentService.attach_alert(
            db=Mock(),
            incident=build_incident(),
            alert_id=7,
        )


@patch(
    "app.services.incident_service."
    "AlertRepository.get_by_id"
)
def test_attach_alert_rejects_missing_alert(
    get_alert_mock: Mock,
) -> None:
    get_alert_mock.return_value = None

    with pytest.raises(
        IncidentAlertNotFoundError
    ):
        IncidentService.attach_alert(
            db=Mock(),
            incident=build_incident(),
            alert_id=404,
        )


@patch(
    "app.services.incident_service."
    "IncidentRepository.detach_alert"
)
def test_detach_alert_rejects_missing_association(
    detach_mock: Mock,
) -> None:
    detach_mock.return_value = False

    with pytest.raises(
        IncidentAlertNotAttachedError
    ):
        IncidentService.detach_alert(
            db=Mock(),
            incident=build_incident(),
            alert_id=8,
        )


@patch(
    "app.services.incident_service."
    "IncidentRepository.get_affected_device_count"
)
@patch(
    "app.services.incident_service."
    "IncidentRepository.count_alerts"
)
def test_statistics_calculate_duration(
    count_alerts_mock: Mock,
    device_count_mock: Mock,
) -> None:
    incident = build_incident()

    count_alerts_mock.return_value = 6
    device_count_mock.return_value = 3

    now = (
        incident.started_at
        + timedelta(minutes=15)
    )

    result = IncidentService.get_statistics(
        db=Mock(),
        incident=incident,
        now=now,
    )

    assert result.alert_count == 6
    assert result.affected_device_count == 3
    assert result.duration_seconds == 900.0
    assert result.is_active is True