"""Tests for packet loss burst incident orchestration."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.core.analytics import (
    AnalyticsSeverity,
    BurstStatus,
)
from app.models.alert import (
    AlertSeverity,
    AlertType,
)
from app.models.incident import (
    IncidentPriority,
    IncidentSeverity,
    IncidentSource,
)
from app.services.alert_deduplication_service import (
    AlertDeduplicationResult,
)
from app.services.metric_series_service import (
    MetricSeriesResult,
)
from app.services.packet_loss_burst_application_service import (
    PacketLossBurstApplicationResult,
)
from app.services.packet_loss_burst_incident_service import (
    PacketLossBurstIncidentService,
)
from app.services.packet_loss_burst_service import (
    PacketLossBurstAnalysisResult,
    PacketLossBurstResult,
)


NOW = datetime(
    2026,
    7,
    16,
    12,
    0,
    tzinfo=UTC,
)


def build_analysis_result(
    *,
    active: bool,
    severity: AnalyticsSeverity = (
        AnalyticsSeverity.CRITICAL
    ),
) -> PacketLossBurstApplicationResult:
    """Build an application analysis result."""

    bursts = []

    if active:
        bursts.append(
            PacketLossBurstResult(
                start_at=NOW,
                end_at=NOW,
                duration_seconds=60.0,
                sample_count=3,
                average_packet_loss_percent=18.0,
                peak_packet_loss_percent=25.0,
                severity=severity,
                status=BurstStatus.ACTIVE,
            )
        )

    analysis = PacketLossBurstAnalysisResult(
        burst_detected=active,
        current_burst_active=active,
        severity=(
            severity
            if active
            else AnalyticsSeverity.NORMAL
        ),
        samples_analyzed=3,
        measured_samples=3,
        missing_samples=0,
        burst_count=len(bursts),
        longest_burst_samples=(
            3
            if active
            else 0
        ),
        peak_packet_loss_percent=(
            25.0
            if active
            else 0.0
        ),
        average_packet_loss_percent=(
            18.0
            if active
            else 0.0
        ),
        warning_threshold_percent=5.0,
        critical_threshold_percent=20.0,
        minimum_consecutive_samples=3,
        maximum_gap_seconds=120,
        bursts=bursts,
    )

    return PacketLossBurstApplicationResult(
        device_id=10,
        series=SimpleNamespace(
            samples=[],
        ),
        analysis=analysis,
    )


@patch(
    "app.services.packet_loss_burst_incident_service."
    "PacketLossBurstApplicationService.analyze"
)
def test_no_active_burst_creates_nothing(
    analyze_mock: Mock,
) -> None:
    analyze_mock.return_value = (
        build_analysis_result(
            active=False
        )
    )

    result = (
        PacketLossBurstIncidentService.evaluate(
            db=Mock(),
            device_id=10,
            device_name="Router Madrid",
        )
    )

    assert result.alert is None
    assert result.incident is None
    assert result.alert_created is False
    assert result.incident_created is False


@patch(
    "app.services.packet_loss_burst_incident_service."
    "IncidentService.create"
)
@patch(
    "app.services.packet_loss_burst_incident_service."
    "IncidentRepository.get_alert_link"
)
@patch(
    "app.services.packet_loss_burst_incident_service."
    "AlertDeduplicationService.create_or_update"
)
@patch(
    "app.services.packet_loss_burst_incident_service."
    "PacketLossBurstApplicationService.analyze"
)
def test_active_burst_creates_alert_and_incident(
    analyze_mock: Mock,
    deduplicate_mock: Mock,
    get_link_mock: Mock,
    create_incident_mock: Mock,
) -> None:
    db = Mock()

    analyze_mock.return_value = (
        build_analysis_result(
            active=True
        )
    )

    alert = SimpleNamespace(
        id=50,
    )

    deduplicate_mock.return_value = (
        AlertDeduplicationResult(
            alert=alert,
            created=True,
            deduplicated=False,
            severity_escalated=False,
        )
    )

    get_link_mock.return_value = None

    incident = SimpleNamespace(
        id=8,
        public_id="INC-2026-000008",
    )

    create_incident_mock.return_value = incident

    result = (
        PacketLossBurstIncidentService.evaluate(
            db=db,
            device_id=10,
            device_name="Router Madrid",
        )
    )

    assert result.alert is alert
    assert result.incident is incident
    assert result.alert_created is True
    assert result.incident_created is True

    deduplicate_mock.assert_called_once_with(
        db=db,
        device_id=10,
        alert_type=AlertType.PACKET_LOSS_BURST,
        severity=AlertSeverity.CRITICAL,
        message=(
            "Active packet loss burst on Router Madrid: "
            "3 consecutive samples, "
            "25.00% peak, "
            "18.00% average"
        ),
    )

    incident_payload = (
        create_incident_mock
        .call_args
        .kwargs["incident_data"]
    )

    assert (
        incident_payload.severity
        == IncidentSeverity.CRITICAL
    )
    assert (
        incident_payload.priority
        == IncidentPriority.CRITICAL
    )
    assert (
        incident_payload.source
        == IncidentSource.ALERT_ENGINE
    )
    assert incident_payload.alert_ids == [
        50,
    ]
    assert (
        incident_payload.metadata["device_id"]
        == 10
    )


@patch(
    "app.services.packet_loss_burst_incident_service."
    "IncidentService.create"
)
@patch(
    "app.services.packet_loss_burst_incident_service."
    "IncidentRepository.get_alert_link"
)
@patch(
    "app.services.packet_loss_burst_incident_service."
    "AlertDeduplicationService.create_or_update"
)
@patch(
    "app.services.packet_loss_burst_incident_service."
    "PacketLossBurstApplicationService.analyze"
)
def test_existing_alert_link_reuses_incident(
    analyze_mock: Mock,
    deduplicate_mock: Mock,
    get_link_mock: Mock,
    create_incident_mock: Mock,
) -> None:
    analyze_mock.return_value = (
        build_analysis_result(
            active=True,
            severity=AnalyticsSeverity.WARNING,
        )
    )

    alert = SimpleNamespace(
        id=51,
    )

    deduplicate_mock.return_value = (
        AlertDeduplicationResult(
            alert=alert,
            created=False,
            deduplicated=True,
            severity_escalated=False,
        )
    )

    incident = SimpleNamespace(
        id=9,
        public_id="INC-2026-000009",
    )

    get_link_mock.return_value = (
        SimpleNamespace(
            incident=incident,
        )
    )

    result = (
        PacketLossBurstIncidentService.evaluate(
            db=Mock(),
            device_id=10,
            device_name="Router Madrid",
        )
    )

    assert result.alert is alert
    assert result.incident is incident
    assert result.alert_created is False
    assert result.alert_deduplicated is True
    assert result.incident_created is False

    create_incident_mock.assert_not_called()