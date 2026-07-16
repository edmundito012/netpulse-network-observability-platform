"""Integration tests for IncidentRepository."""

from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionLocal
from app.models.alert import (
    Alert,
    AlertSeverity,
    AlertStatus,
    AlertType,
)
from app.models.device import (
    Device,
    DeviceStatus,
)
from app.models.incident import (
    IncidentPriority,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)
from app.repositories.incident_repository import (
    IncidentRepository,
)


def create_device(
    db,
    *,
    suffix: str | None = None,
) -> Device:
    """Persist a device with a valid unique IPv4 address."""

    unique_id = suffix or uuid4().hex

    second_octet = int(
        unique_id[:2],
        16,
    )
    third_octet = int(
        unique_id[2:4],
        16,
    )
    fourth_octet = int(
        unique_id[4:6],
        16,
    )

    device = Device(
        name=f"incident-device-{unique_id}",
        ip_address=(
            f"10.{second_octet}."
            f"{third_octet}."
            f"{fourth_octet}"
        ),
        hostname=(
            f"incident-device-{unique_id}"
        ),
        device_type="router",
        location="incident-test",
        status=DeviceStatus.ONLINE,
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return device


def create_alert(
    db,
    *,
    device_id: int,
    message: str = "Incident test alert",
    alert_type: AlertType = AlertType.PACKET_LOSS,
) -> Alert:
    """Persist an alert used as incident evidence."""

    alert = Alert(
        device_id=device_id,
        alert_type=alert_type,
        deduplication_key=(
            f"incident-test:"
            f"{device_id}:"
            f"{uuid4().hex}"
        ),
        severity=AlertSeverity.CRITICAL,
        status=AlertStatus.OPEN,
        message=message,
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return alert


def test_create_incident_generates_public_id() -> None:
    db = SessionLocal()

    try:
        incident = IncidentRepository.create(
            db=db,
            title="WAN degradation in Madrid",
            description=(
                "Packet loss affecting headquarters."
            ),
            severity=IncidentSeverity.CRITICAL,
            priority=IncidentPriority.HIGH,
            source=IncidentSource.ALERT_ENGINE,
            business_impact=(
                "Video conferencing is degraded."
            ),
            tags=[
                "wan",
                "madrid",
            ],
            incident_metadata={
                "detector": "packet_loss_burst",
            },
        )

        assert incident.id is not None
        assert incident.public_id.startswith(
            "INC-"
        )
        assert incident.status == IncidentStatus.OPEN
        assert (
            incident.severity
            == IncidentSeverity.CRITICAL
        )
        assert (
            incident.priority
            == IncidentPriority.HIGH
        )
        assert incident.tags == [
            "wan",
            "madrid",
        ]
        assert incident.incident_metadata == {
            "detector": "packet_loss_burst",
        }
        assert incident.started_at is not None
        assert incident.detected_at is not None
    finally:
        db.close()


def test_get_incident_by_public_id() -> None:
    db = SessionLocal()

    try:
        created = IncidentRepository.create(
            db=db,
            title="Public ID lookup incident",
        )

        result = (
            IncidentRepository
            .get_by_public_id(
                db=db,
                public_id=created.public_id,
            )
        )

        assert result is not None
        assert result.id == created.id
        assert (
            result.public_id
            == created.public_id
        )
    finally:
        db.close()


def test_paginated_incidents_support_filters() -> None:
    db = SessionLocal()

    try:
        IncidentRepository.create(
            db=db,
            title="Critical filtered incident",
            severity=IncidentSeverity.CRITICAL,
            priority=IncidentPriority.CRITICAL,
            source=IncidentSource.ALERT_ENGINE,
        )

        IncidentRepository.create(
            db=db,
            title="Informational filtered incident",
            severity=IncidentSeverity.INFO,
            priority=IncidentPriority.LOW,
            source=IncidentSource.MANUAL,
        )

        result = IncidentRepository.get_paginated(
            db=db,
            severity=IncidentSeverity.CRITICAL,
            source=IncidentSource.ALERT_ENGINE,
            page=1,
            page_size=100,
        )

        items = result["items"]

        assert result["total_count"] >= 1
        assert result["page"] == 1
        assert result["page_size"] == 100

        assert all(
            incident.severity
            == IncidentSeverity.CRITICAL
            for incident in items
        )

        assert all(
            incident.source
            == IncidentSource.ALERT_ENGINE
            for incident in items
        )
    finally:
        db.close()


def test_update_incident_details() -> None:
    db = SessionLocal()

    try:
        incident = IncidentRepository.create(
            db=db,
            title="Initial incident title",
        )

        updated = IncidentRepository.update_details(
            db=db,
            incident=incident,
            title="Updated incident title",
            severity=IncidentSeverity.CRITICAL,
            priority=IncidentPriority.HIGH,
            business_impact=(
                "Headquarters connectivity affected."
            ),
            root_cause="Upstream WAN router",
            tags=[
                "wan",
                "critical",
            ],
            incident_metadata={
                "confidence": 0.91,
            },
        )

        assert (
            updated.title
            == "Updated incident title"
        )
        assert (
            updated.severity
            == IncidentSeverity.CRITICAL
        )
        assert (
            updated.priority
            == IncidentPriority.HIGH
        )
        assert (
            updated.business_impact
            == (
                "Headquarters connectivity "
                "affected."
            )
        )
        assert (
            updated.root_cause
            == "Upstream WAN router"
        )
        assert updated.tags == [
            "wan",
            "critical",
        ]
        assert updated.incident_metadata == {
            "confidence": 0.91,
        }
    finally:
        db.close()


def test_attach_and_detach_alert() -> None:
    db = SessionLocal()

    try:
        device = create_device(db)

        alert = create_alert(
            db,
            device_id=device.id,
        )

        incident = IncidentRepository.create(
            db=db,
            title="Incident with attached alert",
        )

        link = IncidentRepository.attach_alert(
            db=db,
            incident_id=incident.id,
            alert_id=alert.id,
        )

        assert link.id is not None
        assert link.incident_id == incident.id
        assert link.alert_id == alert.id

        assert (
            IncidentRepository.count_alerts(
                db=db,
                incident_id=incident.id,
            )
            == 1
        )

        stored_incident = (
            IncidentRepository.get_by_id(
                db=db,
                incident_id=incident.id,
            )
        )

        assert stored_incident is not None
        assert len(
            stored_incident.alert_links
        ) == 1
        assert (
            stored_incident
            .alert_links[0]
            .alert
            .id
            == alert.id
        )

        detached = (
            IncidentRepository.detach_alert(
                db=db,
                incident_id=incident.id,
                alert_id=alert.id,
            )
        )

        assert detached is True

        assert (
            IncidentRepository.count_alerts(
                db=db,
                incident_id=incident.id,
            )
            == 0
        )

        assert (
            IncidentRepository.detach_alert(
                db=db,
                incident_id=incident.id,
                alert_id=alert.id,
            )
            is False
        )
    finally:
        db.close()


def test_alert_cannot_belong_to_two_incidents() -> None:
    db = SessionLocal()

    try:
        device = create_device(db)

        alert = create_alert(
            db,
            device_id=device.id,
        )

        first_incident = IncidentRepository.create(
            db=db,
            title="First incident",
        )

        second_incident = IncidentRepository.create(
            db=db,
            title="Second incident",
        )

        IncidentRepository.attach_alert(
            db=db,
            incident_id=first_incident.id,
            alert_id=alert.id,
        )

        with pytest.raises(IntegrityError):
            IncidentRepository.attach_alert(
                db=db,
                incident_id=second_incident.id,
                alert_id=alert.id,
            )

        db.rollback()

        existing_link = (
            IncidentRepository.get_alert_link(
                db=db,
                alert_id=alert.id,
            )
        )

        assert existing_link is not None
        assert (
            existing_link.incident_id
            == first_incident.id
        )
    finally:
        db.close()


def test_affected_device_count_uses_distinct_devices() -> None:
    db = SessionLocal()

    try:
        first_device = create_device(db)
        second_device = create_device(db)

        first_alert = create_alert(
            db,
            device_id=first_device.id,
            message="First device alert",
        )

        second_alert = create_alert(
            db,
            device_id=first_device.id,
            message="Repeated first device alert",
            alert_type=AlertType.LATENCY_TREND,
        )

        third_alert = create_alert(
            db,
            device_id=second_device.id,
            message="Second device alert",
        )

        incident = IncidentRepository.create(
            db=db,
            title="Multi-device incident",
        )

        for alert in (
            first_alert,
            second_alert,
            third_alert,
        ):
            IncidentRepository.attach_alert(
                db=db,
                incident_id=incident.id,
                alert_id=alert.id,
            )

        assert (
            IncidentRepository.count_alerts(
                db=db,
                incident_id=incident.id,
            )
            == 3
        )

        assert (
            IncidentRepository
            .get_affected_device_count(
                db=db,
                incident_id=incident.id,
            )
            == 2
        )
    finally:
        db.close()


@pytest.mark.parametrize(
    ("page", "page_size"),
    [
        (0, 20),
        (1, 0),
        (1, 101),
    ],
)
def test_invalid_pagination_is_rejected(
    page: int,
    page_size: int,
) -> None:
    db = SessionLocal()

    try:
        with pytest.raises(ValueError):
            IncidentRepository.get_paginated(
                db=db,
                page=page,
                page_size=page_size,
            )
    finally:
        db.close()