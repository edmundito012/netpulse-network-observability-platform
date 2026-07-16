"""Unit tests for incident response transformation."""

from datetime import UTC, datetime
from types import SimpleNamespace

from app.models.alert import (
    AlertSeverity,
    AlertStatus,
    AlertType,
)
from app.models.incident import (
    IncidentPriority,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)
from app.services.incident_response_service import (
    IncidentResponseService,
)
from app.services.incident_service import (
    IncidentStatistics,
)


NOW = datetime(
    2026,
    7,
    16,
    12,
    0,
    tzinfo=UTC,
)


def build_incident():
    """Build a complete incident test double."""

    alert = SimpleNamespace(
        id=7,
        device_id=12,
        alert_type=AlertType.PACKET_LOSS,
        severity=AlertSeverity.CRITICAL,
        status=AlertStatus.OPEN,
        message="Packet loss detected",
        occurrence_count=3,
        first_seen_at=NOW,
        last_seen_at=NOW,
        created_at=NOW,
        resolved_at=None,
    )

    link = SimpleNamespace(
        alert=alert,
        attached_at=NOW,
    )

    return SimpleNamespace(
        id=1,
        public_id="INC-2026-000001",
        title="WAN degradation",
        description="Madrid office affected",
        status=IncidentStatus.OPEN,
        severity=IncidentSeverity.CRITICAL,
        priority=IncidentPriority.HIGH,
        source=IncidentSource.ALERT_ENGINE,
        owner_id=None,
        business_impact="Video calls degraded",
        root_cause=None,
        resolution_summary=None,
        tags=[
            "wan",
            "madrid",
        ],
        incident_metadata={
            "confidence": 0.91,
        },
        started_at=NOW,
        detected_at=NOW,
        acknowledged_at=None,
        resolved_at=None,
        created_at=NOW,
        updated_at=NOW,
        alert_links=[
            link,
        ],
    )


def test_to_read_includes_attached_alerts() -> None:
    result = IncidentResponseService.to_read(
        build_incident()
    )

    assert result.public_id == (
        "INC-2026-000001"
    )
    assert result.metadata == {
        "confidence": 0.91,
    }
    assert len(result.alerts) == 1
    assert result.alerts[0].id == 7
    assert (
        result.alerts[0].alert_type
        == AlertType.PACKET_LOSS
    )


def test_to_summary_calculates_alert_count() -> None:
    result = (
        IncidentResponseService.to_summary(
            build_incident()
        )
    )

    assert result.alert_count == 1
    assert (
        result.severity
        == IncidentSeverity.CRITICAL
    )


def test_to_statistics_maps_domain_result() -> None:
    statistics = IncidentStatistics(
        incident_id=1,
        public_id="INC-2026-000001",
        alert_count=4,
        affected_device_count=2,
        duration_seconds=600.0,
        is_active=True,
    )

    result = (
        IncidentResponseService
        .to_statistics(statistics)
    )

    assert result.alert_count == 4
    assert result.affected_device_count == 2
    assert result.duration_seconds == 600.0
    assert result.is_active is True