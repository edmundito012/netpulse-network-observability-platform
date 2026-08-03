"""Integration tests for IncidentCorrelationService."""

from datetime import (
    UTC,
    datetime,
)
from uuid import uuid4

import pytest

from app.core.correlation import (
    CorrelationConfiguration,
    CorrelationOutcome,
    CorrelationReason,
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
from app.services.incident_correlation_service import (
    IncidentCorrelationService,
    SourceAlertNotFoundError,
)


def create_device(db) -> Device:
    """Persist a unique device."""

    suffix = uuid4().hex

    device = Device(
        name=f"service-device-{suffix}",
        hostname=f"service-device-{suffix}",
        ip_address=(
            f"10."
            f"{int(suffix[:2], 16)}."
            f"{int(suffix[2:4], 16)}."
            f"{int(suffix[4:6], 16)}"
        ),
        device_type="router",
        location="correlation-service-test",
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
            f"correlation-service:"
            f"{device_id}:"
            f"{uuid4().hex}"
        ),
        severity=severity,
        status=AlertStatus.OPEN,
        message="Incident correlation service test",
        created_at=now,
        first_seen_at=now,
        last_seen_at=now,
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return alert


def test_evaluate_matches_strong_candidate() -> None:
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
            title="Strong correlation candidate",
            severity=IncidentSeverity.CRITICAL,
            source=IncidentSource.ALERT_ENGINE,
        )

        IncidentRepository.attach_alert(
            db=db,
            incident_id=incident.id,
            alert_id=existing_alert.id,
        )

        result = (
            IncidentCorrelationService.evaluate(
                db=db,
                source_alert_id=source_alert.id,
            )
        )

        assert (
            result.outcome
            == CorrelationOutcome.MATCHED_EXISTING
        )

        assert result.correlated is True

        assert (
            result.target_incident_id
            == incident.id
        )

        assert result.score >= 0.65

        assert (
            CorrelationReason.SAME_DEVICE
            in result.reasons
        )

        assert result.candidate_count >= 1
    finally:
        db.close()


def test_evaluate_recommends_new_incident_without_candidates() -> None:
    db = SessionLocal()

    try:
        device = create_device(db)

        source_alert = create_alert(
            db,
            device_id=device.id,
            alert_type=AlertType.PREDICTIVE,
        )

        result = (
            IncidentCorrelationService.evaluate(
                db=db,
                source_alert_id=source_alert.id,
            )
        )

        assert (
            result.outcome
            == CorrelationOutcome.CREATE_NEW
        )

        assert result.correlated is False
        assert result.target_incident_id is None
        assert result.candidate_count == 0

        assert (
            CorrelationReason
            .NO_CANDIDATE_INCIDENT
            in result.reasons
        )
    finally:
        db.close()


def test_evaluate_and_persist_is_idempotent() -> None:
    db = SessionLocal()

    try:
        device = create_device(db)

        source_alert = create_alert(
            db,
            device_id=device.id,
            alert_type=AlertType.JITTER,
        )

        configuration = CorrelationConfiguration(
            window_seconds=900,
            threshold=0.65,
            max_candidates=25,
        )

        (
            first_result,
            first_correlation,
            first_created,
        ) = (
            IncidentCorrelationService
            .evaluate_and_persist(
                db=db,
                source_alert_id=source_alert.id,
                configuration=configuration,
            )
        )

        (
            second_result,
            second_correlation,
            second_created,
        ) = (
            IncidentCorrelationService
            .evaluate_and_persist(
                db=db,
                source_alert_id=source_alert.id,
                configuration=configuration,
            )
        )

        assert first_created is True
        assert second_created is False

        assert (
            second_correlation.id
            == first_correlation.id
        )

        assert (
            second_result.outcome
            == first_result.outcome
        )
    finally:
        db.close()


def test_configuration_change_creates_new_evaluation() -> None:
    db = SessionLocal()

    try:
        device = create_device(db)

        source_alert = create_alert(
            db,
            device_id=device.id,
            alert_type=AlertType.FLAPPING,
        )

        _, first, first_created = (
            IncidentCorrelationService
            .evaluate_and_persist(
                db=db,
                source_alert_id=source_alert.id,
                configuration=(
                    CorrelationConfiguration(
                        threshold=0.65,
                    )
                ),
            )
        )

        _, second, second_created = (
            IncidentCorrelationService
            .evaluate_and_persist(
                db=db,
                source_alert_id=source_alert.id,
                configuration=(
                    CorrelationConfiguration(
                        threshold=0.75,
                    )
                ),
            )
        )

        assert first_created is True
        assert second_created is True
        assert first.id != second.id

        assert (
            first.correlation_key
            != second.correlation_key
        )
    finally:
        db.close()


def test_missing_source_alert_raises_error() -> None:
    db = SessionLocal()

    try:
        with pytest.raises(
            SourceAlertNotFoundError,
            match="was not found",
        ):
            IncidentCorrelationService.evaluate(
                db=db,
                source_alert_id=2_147_483_647,
            )
    finally:
        db.close()


def test_correlation_key_is_deterministic() -> None:
    configuration = CorrelationConfiguration(
        window_seconds=900,
        threshold=0.65,
        max_candidates=25,
    )

    first = (
        IncidentCorrelationService
        .build_correlation_key(
            source_alert_id=50,
            configuration=configuration,
        )
    )

    second = (
        IncidentCorrelationService
        .build_correlation_key(
            source_alert_id=50,
            configuration=configuration,
        )
    )

    assert first == second

    assert first.startswith(
        "correlation:v1:alert:50:"
    )