"""Integration tests for IncidentCorrelationRepository."""

from datetime import (
    UTC,
    datetime,
)
from uuid import uuid4

from app.core.correlation import (
    CorrelationOutcome,
    CorrelationReason,
    CorrelationSignalFamily,
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
from app.repositories.incident_correlation_repository import (
    IncidentCorrelationRepository,
)
from app.repositories.incident_repository import (
    IncidentRepository,
)


def create_device(db) -> Device:
    """Persist a unique test device."""

    suffix = uuid4().hex

    device = Device(
        name=f"correlation-device-{suffix}",
        hostname=f"correlation-device-{suffix}",
        ip_address=(
            f"10."
            f"{int(suffix[:2], 16)}."
            f"{int(suffix[2:4], 16)}."
            f"{int(suffix[4:6], 16)}"
        ),
        device_type="router",
        location="correlation-test",
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
) -> Alert:
    """Persist a correlation test alert."""

    now = datetime.now(UTC)

    alert = Alert(
        device_id=device_id,
        alert_type=alert_type,
        deduplication_key=(
            f"correlation-test:"
            f"{device_id}:"
            f"{uuid4().hex}"
        ),
        severity=AlertSeverity.CRITICAL,
        status=AlertStatus.OPEN,
        message="Correlation repository test alert",
        created_at=now,
        first_seen_at=now,
        last_seen_at=now,
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return alert


def test_create_and_get_by_key() -> None:
    db = SessionLocal()

    try:
        device = create_device(db)

        alert = create_alert(
            db,
            device_id=device.id,
            alert_type=AlertType.PACKET_LOSS,
        )

        correlation_key = (
            f"test-correlation:{uuid4().hex}"
        )

        command = (
            IncidentCorrelationRepository
            .build_create_command(
                correlation_key=correlation_key,
                source_alert_id=alert.id,
                target_incident_id=None,
                outcome=(
                    CorrelationOutcome.CREATE_NEW
                ),
                signal_family=(
                    CorrelationSignalFamily
                    .CONNECTIVITY
                ),
                score=0.0,
                threshold=0.65,
                reasons=[
                    CorrelationReason
                    .NO_CANDIDATE_INCIDENT
                ],
                candidate_count=0,
                window_seconds=900,
                explanation=(
                    "No incident candidate was found."
                ),
                metadata={
                    "test": True,
                },
            )
        )

        created = (
            IncidentCorrelationRepository.create(
                db=db,
                command=command,
            )
        )

        result = (
            IncidentCorrelationRepository
            .get_by_key(
                db=db,
                correlation_key=correlation_key,
            )
        )

        assert result is not None
        assert result.id == created.id

        assert (
            result.outcome
            == CorrelationOutcome.CREATE_NEW
        )

        assert result.reasons == [
            CorrelationReason
            .NO_CANDIDATE_INCIDENT
            .value
        ]

        assert result.correlation_metadata == {
            "test": True,
        }
    finally:
        db.close()


def test_get_or_create_is_idempotent() -> None:
    db = SessionLocal()

    try:
        device = create_device(db)

        alert = create_alert(
            db,
            device_id=device.id,
            alert_type=AlertType.JITTER,
        )

        command = (
            IncidentCorrelationRepository
            .build_create_command(
                correlation_key=(
                    f"idempotent:{uuid4().hex}"
                ),
                source_alert_id=alert.id,
                target_incident_id=None,
                outcome=(
                    CorrelationOutcome.CREATE_NEW
                ),
                signal_family=(
                    CorrelationSignalFamily
                    .PERFORMANCE
                ),
                score=0.25,
                threshold=0.65,
                reasons=[
                    CorrelationReason
                    .SCORE_BELOW_THRESHOLD
                ],
                candidate_count=1,
                window_seconds=900,
                explanation=(
                    "Candidate score was below threshold."
                ),
            )
        )

        first, first_created = (
            IncidentCorrelationRepository
            .get_or_create(
                db=db,
                command=command,
            )
        )

        second, second_created = (
            IncidentCorrelationRepository
            .get_or_create(
                db=db,
                command=command,
            )
        )

        assert first_created is True
        assert second_created is False
        assert second.id == first.id
    finally:
        db.close()


def test_find_candidates_returns_same_device_incident() -> None:
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
            title="Correlation candidate incident",
            severity=IncidentSeverity.CRITICAL,
            source=IncidentSource.ALERT_ENGINE,
        )

        IncidentRepository.attach_alert(
            db=db,
            incident_id=incident.id,
            alert_id=existing_alert.id,
        )

        candidates = (
            IncidentCorrelationRepository
            .find_candidates(
                db=db,
                source_alert=source_alert,
                window_seconds=900,
                limit=25,
            )
        )

        assert any(
            candidate.id == incident.id
            for candidate in candidates
        )
    finally:
        db.close()


def test_paginated_correlations_support_filters() -> None:
    db = SessionLocal()

    try:
        device = create_device(db)

        alert = create_alert(
            db,
            device_id=device.id,
            alert_type=AlertType.FLAPPING,
        )

        command = (
            IncidentCorrelationRepository
            .build_create_command(
                correlation_key=(
                    f"pagination:{uuid4().hex}"
                ),
                source_alert_id=alert.id,
                target_incident_id=None,
                outcome=(
                    CorrelationOutcome.CREATE_NEW
                ),
                signal_family=(
                    CorrelationSignalFamily.STABILITY
                ),
                score=0.0,
                threshold=0.65,
                reasons=[
                    CorrelationReason
                    .NO_CANDIDATE_INCIDENT
                ],
                candidate_count=0,
                window_seconds=900,
                explanation=(
                    "No candidate incident was found."
                ),
            )
        )

        IncidentCorrelationRepository.create(
            db=db,
            command=command,
        )

        result = (
            IncidentCorrelationRepository
            .get_paginated(
                db=db,
                source_alert_id=alert.id,
                outcome=(
                    CorrelationOutcome.CREATE_NEW
                ),
                page=1,
                page_size=20,
            )
        )

        assert result["total_count"] == 1
        assert len(result["items"]) == 1
    finally:
        db.close()