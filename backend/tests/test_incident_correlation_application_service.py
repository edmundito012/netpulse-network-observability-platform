"""Integration tests for correlation decision application."""

from datetime import (
    UTC,
    datetime,
)
from uuid import uuid4

from app.core.correlation import (
    CorrelationApplicationStatus,
    CorrelationConfiguration,
    CorrelationOutcome,
)
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
    IncidentSeverity,
    IncidentSource,
)
from app.repositories.incident_repository import (
    IncidentRepository,
)
from app.services.incident_correlation_application_service import (
    IncidentCorrelationApplicationService,
)


def create_device(db) -> Device:
    """Persist a unique test device."""

    suffix = uuid4().hex

    device = Device(
        name=f"application-device-{suffix}",
        hostname=f"application-device-{suffix}",
        ip_address=(
            f"10."
            f"{int(suffix[:2], 16)}."
            f"{int(suffix[2:4], 16)}."
            f"{int(suffix[4:6], 16)}"
        ),
        device_type="router",
        location="correlation-application-test",
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
    alert_type: AlertType,
    severity: AlertSeverity = (
        AlertSeverity.CRITICAL
    ),
) -> Alert:
    """Persist an alert with explicit timestamps."""

    now = datetime.now(UTC)

    alert = Alert(
        device_id=device_id,
        alert_type=alert_type,
        deduplication_key=(
            f"correlation-application:"
            f"{device_id}:"
            f"{uuid4().hex}"
        ),
        severity=severity,
        status=AlertStatus.OPEN,
        message="Correlation application test alert",
        created_at=now,
        first_seen_at=now,
        last_seen_at=now,
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return alert


def test_apply_match_attaches_alert_to_existing_incident() -> None:
    db = SessionLocal()

    try:
        device = create_device(db)

        existing_alert = create_alert(
            db,
            device_id=device.id,
            alert_type=(
                AlertType.PACKET_LOSS_BURST
            ),
        )

        source_alert = create_alert(
            db,
            device_id=device.id,
            alert_type=AlertType.PACKET_LOSS,
        )

        incident = IncidentRepository.create(
            db=db,
            title="Existing correlation target",
            severity=IncidentSeverity.CRITICAL,
            source=IncidentSource.ALERT_ENGINE,
        )

        IncidentRepository.attach_alert(
            db=db,
            incident_id=incident.id,
            alert_id=existing_alert.id,
        )

        result = (
            IncidentCorrelationApplicationService
            .evaluate_and_apply(
                db=db,
                source_alert_id=source_alert.id,
            )
        )

        assert (
            result.outcome
            == CorrelationOutcome.MATCHED_EXISTING
        )

        assert (
            result.application_status
            == CorrelationApplicationStatus.APPLIED
        )

        assert result.incident_id == incident.id
        assert result.incident_created is False
        assert result.alert_attached is True
        assert result.replayed is False

        link = IncidentRepository.get_alert_link(
            db=db,
            alert_id=source_alert.id,
        )

        assert link is not None
        assert link.incident_id == incident.id
    finally:
        db.close()


def test_apply_create_new_creates_incident() -> None:
    db = SessionLocal()

    try:
        device = create_device(db)

        source_alert = create_alert(
            db,
            device_id=device.id,
            alert_type=AlertType.PREDICTIVE,
            severity=AlertSeverity.WARNING,
        )

        result = (
            IncidentCorrelationApplicationService
            .evaluate_and_apply(
                db=db,
                source_alert_id=source_alert.id,
            )
        )

        assert (
            result.outcome
            == CorrelationOutcome.CREATE_NEW
        )

        assert (
            result.application_status
            == CorrelationApplicationStatus.APPLIED
        )

        assert result.incident_id is not None
        assert result.incident_created is True
        assert result.alert_attached is True

        incident = IncidentRepository.get_by_id(
            db=db,
            incident_id=result.incident_id,
        )

        assert incident is not None

        assert (
            incident.source
            == IncidentSource.CORRELATION_ENGINE
        )

        assert (
            incident.severity
            == IncidentSeverity.WARNING
        )

        link = IncidentRepository.get_alert_link(
            db=db,
            alert_id=source_alert.id,
        )

        assert link is not None
        assert link.incident_id == incident.id
    finally:
        db.close()


def test_repeated_application_is_idempotent() -> None:
    db = SessionLocal()

    try:
        device = create_device(db)

        source_alert = create_alert(
            db,
            device_id=device.id,
            alert_type=AlertType.JITTER,
        )

        configuration = CorrelationConfiguration(
            threshold=0.65,
        )

        first = (
            IncidentCorrelationApplicationService
            .evaluate_and_apply(
                db=db,
                source_alert_id=source_alert.id,
                configuration=configuration,
            )
        )

        second = (
            IncidentCorrelationApplicationService
            .evaluate_and_apply(
                db=db,
                source_alert_id=source_alert.id,
                configuration=configuration,
            )
        )

        assert first.correlation_id == (
            second.correlation_id
        )

        assert first.incident_id == second.incident_id

        assert first.incident_created is True
        assert second.incident_created is True

        assert first.replayed is False
        assert second.replayed is True

        assert second.alert_attached is False
    finally:
        db.close()


def test_configuration_change_can_produce_new_application() -> None:
    db = SessionLocal()

    try:
        first_device = create_device(db)
        second_device = create_device(db)

        first_alert = create_alert(
            db,
            device_id=first_device.id,
            alert_type=AlertType.FLAPPING,
        )

        second_alert = create_alert(
            db,
            device_id=second_device.id,
            alert_type=AlertType.FLAPPING,
        )

        first = (
            IncidentCorrelationApplicationService
            .evaluate_and_apply(
                db=db,
                source_alert_id=first_alert.id,
                configuration=(
                    CorrelationConfiguration(
                        threshold=0.65,
                    )
                ),
            )
        )

        second = (
            IncidentCorrelationApplicationService
            .evaluate_and_apply(
                db=db,
                source_alert_id=second_alert.id,
                configuration=(
                    CorrelationConfiguration(
                        threshold=0.75,
                    )
                ),
            )
        )

        assert first.correlation_id != (
            second.correlation_id
        )

        assert first.incident_id != (
            second.incident_id
        )
    finally:
        db.close()