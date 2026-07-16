"""Unit tests for Incident Engine request schemas."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.incident import (
    IncidentPriority,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)
from app.schemas.incident import (
    IncidentAlertAttachRequest,
    IncidentCreate,
    IncidentLifecycleTransition,
    IncidentResolveRequest,
)


def test_incident_create_normalizes_tags_and_alert_ids() -> None:
    payload = IncidentCreate(
        title="  WAN degradation  ",
        description="  Headquarters affected  ",
        severity=IncidentSeverity.CRITICAL,
        priority=IncidentPriority.HIGH,
        source=IncidentSource.ALERT_ENGINE,
        tags=[
            "WAN",
            " madrid ",
            "wan",
            "",
        ],
        alert_ids=[
            1,
            2,
            1,
        ],
    )

    assert payload.title == "WAN degradation"
    assert payload.description == "Headquarters affected"
    assert payload.tags == [
        "wan",
        "madrid",
    ]
    assert payload.alert_ids == [
        1,
        2,
    ]


def test_incident_create_accepts_operational_dates() -> None:
    started_at = datetime(
        2026,
        7,
        16,
        10,
        0,
        tzinfo=UTC,
    )

    payload = IncidentCreate(
        title="Packet loss affecting Madrid",
        started_at=started_at,
    )

    assert payload.started_at == started_at


def test_incident_create_rejects_invalid_alert_id() -> None:
    with pytest.raises(ValidationError):
        IncidentCreate(
            title="Invalid alert association",
            alert_ids=[
                0,
            ],
        )


def test_alert_attach_request_deduplicates_ids() -> None:
    payload = IncidentAlertAttachRequest(
        alert_ids=[
            10,
            11,
            10,
        ]
    )

    assert payload.alert_ids == [
        10,
        11,
    ]


def test_resolution_requires_summary() -> None:
    with pytest.raises(ValidationError):
        IncidentResolveRequest(
            resolution_summary="  ",
        )


def test_generic_transition_rejects_direct_resolution() -> None:
    with pytest.raises(
        ValidationError,
        match="incident resolution operation",
    ):
        IncidentLifecycleTransition(
            target_status=IncidentStatus.RESOLVED,
        )


def test_generic_transition_accepts_investigating() -> None:
    transition = IncidentLifecycleTransition(
        target_status=(
            IncidentStatus.INVESTIGATING
        ),
    )

    assert (
        transition.target_status
        == IncidentStatus.INVESTIGATING
    )