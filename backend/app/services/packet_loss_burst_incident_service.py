"""Packet loss burst alert and incident orchestration."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.analytics import AnalyticsSeverity
from app.models.alert import (
    Alert,
    AlertSeverity,
    AlertType,
)
from app.models.incident import (
    Incident,
    IncidentPriority,
    IncidentSeverity,
    IncidentSource,
)
from app.repositories.incident_repository import (
    IncidentRepository,
)
from app.schemas.incident import IncidentCreate
from app.services.alert_deduplication_service import (
    AlertDeduplicationService,
)
from app.services.incident_service import IncidentService
from app.services.packet_loss_burst_application_service import (
    PacketLossBurstApplicationResult,
    PacketLossBurstApplicationService,
)
from app.services.packet_loss_burst_service import (
    PacketLossBurstResult,
)


@dataclass(frozen=True, slots=True)
class PacketLossBurstIncidentResult:
    """Outcome of one packet loss burst operational evaluation."""

    analysis_result: PacketLossBurstApplicationResult

    alert: Alert | None
    incident: Incident | None

    alert_created: bool
    alert_deduplicated: bool
    incident_created: bool


class PacketLossBurstIncidentService:
    """Convert active packet loss bursts into operational incidents."""

    DEFAULT_SERIES_LIMIT = 100
    DEFAULT_WARNING_THRESHOLD_PERCENT = 5.0
    DEFAULT_CRITICAL_THRESHOLD_PERCENT = 20.0
    DEFAULT_MINIMUM_CONSECUTIVE_SAMPLES = 3
    DEFAULT_MAXIMUM_GAP_SECONDS = 120

    @classmethod
    def evaluate(
        cls,
        db: Session,
        *,
        device_id: int,
        device_name: str,
    ) -> PacketLossBurstIncidentResult:
        """Evaluate recent metrics and create or reuse alert/incident state."""

        analysis_result = (
            PacketLossBurstApplicationService.analyze(
                db=db,
                device_id=device_id,
                limit=cls.DEFAULT_SERIES_LIMIT,
                warning_threshold_percent=(
                    cls.DEFAULT_WARNING_THRESHOLD_PERCENT
                ),
                critical_threshold_percent=(
                    cls.DEFAULT_CRITICAL_THRESHOLD_PERCENT
                ),
                minimum_consecutive_samples=(
                    cls.DEFAULT_MINIMUM_CONSECUTIVE_SAMPLES
                ),
                maximum_gap_seconds=(
                    cls.DEFAULT_MAXIMUM_GAP_SECONDS
                ),
            )
        )

        active_burst = cls._get_active_burst(
            analysis_result
        )

        if active_burst is None:
            return PacketLossBurstIncidentResult(
                analysis_result=analysis_result,
                alert=None,
                incident=None,
                alert_created=False,
                alert_deduplicated=False,
                incident_created=False,
            )

        alert_severity = cls._to_alert_severity(
            active_burst.severity
        )

        alert_result = (
            AlertDeduplicationService.create_or_update(
                db=db,
                device_id=device_id,
                alert_type=AlertType.PACKET_LOSS_BURST,
                severity=alert_severity,
                message=cls._build_alert_message(
                    device_name=device_name,
                    burst=active_burst,
                ),
            )
        )

        existing_link = (
            IncidentRepository.get_alert_link(
                db=db,
                alert_id=alert_result.alert.id,
            )
        )

        if existing_link is not None:
            return PacketLossBurstIncidentResult(
                analysis_result=analysis_result,
                alert=alert_result.alert,
                incident=existing_link.incident,
                alert_created=alert_result.created,
                alert_deduplicated=(
                    alert_result.deduplicated
                ),
                incident_created=False,
            )

        incident = IncidentService.create(
            db=db,
            incident_data=IncidentCreate(
                title=(
                    "Packet loss burst affecting "
                    f"{device_name}"
                ),
                description=(
                    "NetPulse detected sustained packet loss "
                    f"on device {device_name}. "
                    f"The active burst contains "
                    f"{active_burst.sample_count} samples, "
                    f"peaked at "
                    f"{active_burst.peak_packet_loss_percent:.2f}% "
                    f"and averaged "
                    f"{active_burst.average_packet_loss_percent:.2f}%."
                ),
                severity=cls._to_incident_severity(
                    active_burst.severity
                ),
                priority=cls._to_incident_priority(
                    active_burst.severity
                ),
                source=IncidentSource.ALERT_ENGINE,
                business_impact=(
                    "Sustained packet loss may degrade "
                    "interactive traffic, video calls, "
                    "streaming and application connectivity."
                ),
                started_at=active_burst.start_at,
                tags=[
                    "packet-loss",
                    "burst",
                    "network-degradation",
                ],
                metadata={
                    "detector": "packet_loss_burst",
                    "device_id": device_id,
                    "device_name": device_name,
                    "sample_count": (
                        active_burst.sample_count
                    ),
                    "duration_seconds": (
                        active_burst.duration_seconds
                    ),
                    "peak_packet_loss_percent": (
                        active_burst
                        .peak_packet_loss_percent
                    ),
                    "average_packet_loss_percent": (
                        active_burst
                        .average_packet_loss_percent
                    ),
                },
                alert_ids=[
                    alert_result.alert.id,
                ],
            ),
        )

        return PacketLossBurstIncidentResult(
            analysis_result=analysis_result,
            alert=alert_result.alert,
            incident=incident,
            alert_created=alert_result.created,
            alert_deduplicated=(
                alert_result.deduplicated
            ),
            incident_created=True,
        )

    @staticmethod
    def _get_active_burst(
        analysis_result: PacketLossBurstApplicationResult,
    ) -> PacketLossBurstResult | None:
        """Return the most recent currently active burst."""

        active_bursts = [
            burst
            for burst in analysis_result.analysis.bursts
            if burst.status.value == "ACTIVE"
        ]

        if not active_bursts:
            return None

        return max(
            active_bursts,
            key=lambda burst: (
                burst.end_at,
                burst.start_at,
            ),
        )

    @staticmethod
    def _to_alert_severity(
        severity: AnalyticsSeverity,
    ) -> AlertSeverity:
        """Map analytics severity into alert severity."""

        if severity == AnalyticsSeverity.CRITICAL:
            return AlertSeverity.CRITICAL

        return AlertSeverity.WARNING

    @staticmethod
    def _to_incident_severity(
        severity: AnalyticsSeverity,
    ) -> IncidentSeverity:
        """Map analytics severity into incident severity."""

        if severity == AnalyticsSeverity.CRITICAL:
            return IncidentSeverity.CRITICAL

        return IncidentSeverity.WARNING

    @staticmethod
    def _to_incident_priority(
        severity: AnalyticsSeverity,
    ) -> IncidentPriority:
        """Map burst severity into operational priority."""

        if severity == AnalyticsSeverity.CRITICAL:
            return IncidentPriority.CRITICAL

        return IncidentPriority.HIGH

    @staticmethod
    def _build_alert_message(
        *,
        device_name: str,
        burst: PacketLossBurstResult,
    ) -> str:
        """Build a concise alert message from an active burst."""

        return (
            f"Active packet loss burst on {device_name}: "
            f"{burst.sample_count} consecutive samples, "
            f"{burst.peak_packet_loss_percent:.2f}% peak, "
            f"{burst.average_packet_loss_percent:.2f}% average"
        )