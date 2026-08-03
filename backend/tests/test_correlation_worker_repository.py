"""Tests for correlation worker persistence queries."""

from datetime import (
    UTC,
    datetime,
    timedelta,
)
from uuid import uuid4

import pytest

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
from app.repositories.correlation_worker_repository import (
    CorrelationWorkerRepository,
)
from app.repositories.incident_repository import (
    IncidentRepository,
)
from app.services.incident_correlation_service import (
    IncidentCorrelationService,
)


def create_device(db) -> Device:
    """Persist a unique worker test device."""

    suffix = uuid4().hex

    device = Device(
        name=f"worker-device-{suffix}",
        hostname=f"worker-device-{suffix}",
        ip_address=(
            f"10."
            f"{int(suffix[:2], 16)}."
            f"{int(suffix[2:4], 16)}."
            f"{int(suffix[4:6], 16)}"
        ),
        device_type="router",
        location="correlation-worker-test",
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
    status: AlertStatus = AlertStatus.OPEN,
    alert_type: AlertType = AlertType.JITTER,
    created_at: datetime | None = None,
) -> Alert:
    """Persist one correlation worker test alert."""

    timestamp = (
        created_at
        or datetime.now(UTC)
    )

    alert = Alert(
        device_id=device_id,
        alert_type=alert_type,
        deduplication_key=(
            f"worker:"
            f"{device_id}:"
            f"{uuid4().hex}"
        ),
        severity=AlertSeverity.WARNING,
        status=status,
        message="Correlation worker test alert",
        created_at=timestamp,
        first_seen_at=timestamp,
        last_seen_at=timestamp,
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return alert


def test_get_pending_alert_ids_returns_open_alert() -> None:
    """Return an unattached open alert without correlation history."""

    db = SessionLocal()

    try:
        device = create_device(db)

        alert = create_alert(
            db,
            device_id=device.id,
            created_at=(
                datetime.now(UTC)
                - timedelta(days=3650)
            ),
        )

        result = (
            CorrelationWorkerRepository
            .get_pending_alert_ids(
                db=db,
                limit=500,
            )
        )

        assert alert.id in result

    finally:
        db.close()


def test_get_pending_alert_ids_returns_acknowledged_alert() -> None:
    """Allow acknowledged alerts awaiting their first evaluation."""

    db = SessionLocal()

    try:
        device = create_device(db)

        alert = create_alert(
            db,
            device_id=device.id,
            status=AlertStatus.ACKNOWLEDGED,
            created_at=(
                datetime.now(UTC)
                - timedelta(days=3650)
            ),
        )

        result = (
            CorrelationWorkerRepository
            .get_pending_alert_ids(
                db=db,
                limit=500,
            )
        )

        assert alert.id in result

    finally:
        db.close()


def test_get_pending_alert_ids_excludes_resolved_alert() -> None:
    """Do not process alerts that are already resolved."""

    db = SessionLocal()

    try:
        device = create_device(db)

        alert = create_alert(
            db,
            device_id=device.id,
            status=AlertStatus.RESOLVED,
        )

        result = (
            CorrelationWorkerRepository
            .get_pending_alert_ids(
                db=db,
                limit=500,
            )
        )

        assert alert.id not in result

    finally:
        db.close()


def test_get_pending_alert_ids_excludes_evaluated_alert() -> None:
    """Do not reevaluate an alert with persisted correlation history."""

    db = SessionLocal()

    try:
        device = create_device(db)

        alert = create_alert(
            db,
            device_id=device.id,
        )

        (
            IncidentCorrelationService
            .evaluate_and_persist(
                db=db,
                source_alert_id=alert.id,
            )
        )

        result = (
            CorrelationWorkerRepository
            .get_pending_alert_ids(
                db=db,
                limit=500,
            )
        )

        assert alert.id not in result

    finally:
        db.close()


def test_pending_alerts_exclude_alert_already_attached_to_incident(
) -> None:
    """Do not process an alert already owned by an incident."""

    db = SessionLocal()

    try:
        device = create_device(db)

        alert = create_alert(
            db,
            device_id=device.id,
            created_at=(
                datetime.now(UTC)
                - timedelta(days=3650)
            ),
        )

        incident = IncidentRepository.create(
            db=db,
            title="Existing worker incident",
            severity=IncidentSeverity.WARNING,
            source=IncidentSource.ALERT_ENGINE,
        )

        IncidentRepository.attach_alert(
            db=db,
            incident_id=incident.id,
            alert_id=alert.id,
        )

        result = (
            CorrelationWorkerRepository
            .get_pending_alert_ids(
                db=db,
                limit=500,
            )
        )

        assert alert.id not in result

    finally:
        db.close()


@pytest.mark.parametrize(
    "limit",
    [
        0,
        -1,
        501,
    ],
)
def test_get_pending_alert_ids_validates_limit(
    limit: int,
) -> None:
    """Reject invalid worker batch limits."""

    db = SessionLocal()

    try:
        with pytest.raises(
            ValueError,
            match="between 1 and 500",
        ):
            (
                CorrelationWorkerRepository
                .get_pending_alert_ids(
                    db=db,
                    limit=limit,
                )
            )

    finally:
        db.close()