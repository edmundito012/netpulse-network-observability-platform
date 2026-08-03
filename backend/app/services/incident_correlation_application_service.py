"""Apply persisted Correlation Engine decisions."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.correlation import (
    CorrelationApplicationStatus,
    CorrelationConfiguration,
    CorrelationOutcome,
)
from app.models.alert import (
    Alert,
    AlertSeverity,
)
from app.models.incident import (
    Incident,
    IncidentPriority,
    IncidentSeverity,
    IncidentSource,
)
from app.models.incident_timeline_event import (
    IncidentTimelineActorType,
)
from app.repositories.incident_correlation_repository import (
    IncidentCorrelationRepository,
)
from app.repositories.incident_repository import (
    IncidentRepository,
)
from app.schemas.incident import IncidentCreate
from app.schemas.incident_correlation_application import (
    CorrelationApplicationResult,
)
from app.services.incident_correlation_service import (
    IncidentCorrelationService,
)
from app.services.incident_service import (
    IncidentService,
)


class CorrelationApplicationError(RuntimeError):
    """Base error raised while applying a correlation decision."""


class CorrelationTargetIncidentMissingError(
    CorrelationApplicationError
):
    """Raised when a matched correlation has no usable target."""


class IncidentCorrelationApplicationService:
    """Evaluate, persist and apply one correlation decision."""

    ACTOR_LABEL = "NetPulse Correlation Engine"

    @classmethod
    def evaluate_and_apply(
        cls,
        db: Session,
        *,
        source_alert_id: int,
        configuration: (
            CorrelationConfiguration | None
        ) = None,
    ) -> CorrelationApplicationResult:
        """Evaluate an alert and apply its persisted decision."""

        (
            evaluation,
            correlation,
            _,
        ) = (
            IncidentCorrelationService
            .evaluate_and_persist(
                db=db,
                source_alert_id=source_alert_id,
                configuration=configuration,
            )
        )

        if (
            correlation.application_status
            == CorrelationApplicationStatus.APPLIED
        ):
            return cls._build_replayed_result(
                correlation=correlation,
            )

        try:
            if (
                evaluation.outcome
                == CorrelationOutcome.MATCHED_EXISTING
            ):
                return cls._apply_existing_match(
                    db=db,
                    source_alert_id=source_alert_id,
                    correlation=correlation,
                )

            if (
                evaluation.outcome
                == CorrelationOutcome.CREATE_NEW
            ):
                return cls._apply_new_incident(
                    db=db,
                    source_alert_id=source_alert_id,
                    correlation=correlation,
                )

            return cls._apply_no_action(
                db=db,
                source_alert_id=source_alert_id,
                correlation=correlation,
            )

        except Exception as exc:
            cls._record_failure(
                db=db,
                correlation=correlation,
                exc=exc,
            )

            raise

    @classmethod
    def _apply_existing_match(
        cls,
        db: Session,
        *,
        source_alert_id: int,
        correlation,
    ) -> CorrelationApplicationResult:
        """Attach the source alert to the selected incident."""

        target_incident_id = (
            correlation.target_incident_id
        )

        if target_incident_id is None:
            raise CorrelationTargetIncidentMissingError(
                "MATCHED_EXISTING correlation "
                "does not contain a target incident"
            )

        incident = (
            IncidentRepository.get_by_id(
                db=db,
                incident_id=target_incident_id,
            )
        )

        if incident is None:
            raise CorrelationTargetIncidentMissingError(
                "correlation target incident "
                f"{target_incident_id} was not found"
            )

        existing_link = (
            IncidentRepository.get_alert_link(
                db=db,
                alert_id=source_alert_id,
            )
        )

        already_attached = (
            existing_link is not None
            and existing_link.incident_id
            == incident.id
        )

        IncidentService.attach_alert(
            db=db,
            incident=incident,
            alert_id=source_alert_id,
            actor_type=(
                IncidentTimelineActorType.SYSTEM
            ),
            actor_label=cls.ACTOR_LABEL,
        )

        attached_now = not already_attached

        applied = (
            IncidentCorrelationRepository
            .mark_applied(
                db=db,
                correlation=correlation,
                applied_incident_id=incident.id,
                applied_incident_public_id=(
                    incident.public_id
                ),
                incident_created=False,
                alert_attached=attached_now,
            )
        )

        return CorrelationApplicationResult(
            correlation_id=applied.id,
            source_alert_id=source_alert_id,
            outcome=applied.outcome,
            application_status=(
                applied.application_status
            ),
            incident_id=incident.id,
            incident_public_id=incident.public_id,
            incident_created=False,
            alert_attached=attached_now,
            replayed=False,
        )

    @classmethod
    def _apply_new_incident(
        cls,
        db: Session,
        *,
        source_alert_id: int,
        correlation,
    ) -> CorrelationApplicationResult:
        """Create a new incident containing the source alert."""

        source_alert = cls._get_source_alert(
            correlation=correlation,
        )

        incident_data = IncidentCreate(
            title=cls._build_incident_title(
                source_alert
            ),
            description=(
                "Incident created automatically by the "
                "Correlation Engine after no existing "
                "incident reached the configured threshold. "
                f"Source alert: {source_alert.id}. "
                f"{correlation.explanation}"
            ),
            severity=cls._map_severity(
                source_alert.severity
            ),
            priority=cls._map_priority(
                source_alert.severity
            ),
            source=(
                IncidentSource.CORRELATION_ENGINE
            ),
            started_at=(
                source_alert.first_seen_at
                or source_alert.created_at
            ),
            tags=[
                "correlation-engine",
                cls._normalize_tag(
                    source_alert.alert_type.value
                ),
            ],
            metadata={
                "correlation_id": correlation.id,
                "correlation_key": (
                    correlation.correlation_key
                ),
                "source_alert_id": source_alert.id,
                "correlation_score": str(
                    correlation.score
                ),
                "correlation_threshold": str(
                    correlation.threshold
                ),
                "signal_family": (
                    correlation.signal_family.value
                ),
            },
            alert_ids=[
                source_alert.id,
            ],
        )

        incident = IncidentService.create(
            db=db,
            incident_data=incident_data,
        )

        applied = (
            IncidentCorrelationRepository
            .mark_applied(
                db=db,
                correlation=correlation,
                applied_incident_id=incident.id,
                applied_incident_public_id=(
                    incident.public_id
                ),
                incident_created=True,
                alert_attached=True,
            )
        )

        return CorrelationApplicationResult(
            correlation_id=applied.id,
            source_alert_id=source_alert_id,
            outcome=applied.outcome,
            application_status=(
                applied.application_status
            ),
            incident_id=incident.id,
            incident_public_id=incident.public_id,
            incident_created=True,
            alert_attached=True,
            replayed=False,
        )

    @staticmethod
    def _apply_no_action(
        db: Session,
        *,
        source_alert_id: int,
        correlation,
    ) -> CorrelationApplicationResult:
        """Mark a NO_ACTION decision as applied."""

        applied = (
            IncidentCorrelationRepository
            .mark_applied(
                db=db,
                correlation=correlation,
                applied_incident_id=None,
                applied_incident_public_id=None,
                incident_created=False,
                alert_attached=False,
            )
        )

        return CorrelationApplicationResult(
            correlation_id=applied.id,
            source_alert_id=source_alert_id,
            outcome=applied.outcome,
            application_status=(
                applied.application_status
            ),
            incident_id=None,
            incident_public_id=None,
            incident_created=False,
            alert_attached=False,
            replayed=False,
        )

    @staticmethod
    def _build_replayed_result(
        *,
        correlation,
    ) -> CorrelationApplicationResult:
        """Return the result stored by an earlier application."""

        metadata = dict(
            correlation.correlation_metadata or {}
        )

        incident_id = metadata.get(
            "applied_incident_id"
        )

        incident_public_id = metadata.get(
            "applied_incident_public_id"
        )

        return CorrelationApplicationResult(
            correlation_id=correlation.id,
            source_alert_id=(
                correlation.source_alert_id
            ),
            outcome=correlation.outcome,
            application_status=(
                correlation.application_status
            ),
            incident_id=incident_id,
            incident_public_id=incident_public_id,
            incident_created=bool(
                metadata.get(
                    "incident_created",
                    False,
                )
            ),
            alert_attached=False,
            replayed=True,
        )

    @staticmethod
    def _get_source_alert(
        *,
        correlation,
    ) -> Alert:
        """Return the loaded source alert."""

        source_alert = correlation.source_alert

        if source_alert is None:
            raise CorrelationApplicationError(
                "correlation source alert "
                f"{correlation.source_alert_id} "
                "could not be loaded"
            )

        return source_alert

    @staticmethod
    def _build_incident_title(
        alert: Alert,
    ) -> str:
        """Build a stable operator-friendly incident title."""

        readable_type = (
            alert.alert_type.value
            .replace("_", " ")
            .lower()
        )

        return (
            f"{readable_type.capitalize()} "
            f"detected on device {alert.device_id}"
        )

    @staticmethod
    def _map_severity(
        alert_severity: AlertSeverity,
    ) -> IncidentSeverity:
        """Map alert severity to incident severity."""

        mapping = {
            AlertSeverity.CRITICAL: (
                IncidentSeverity.CRITICAL
            ),
            AlertSeverity.WARNING: (
                IncidentSeverity.WARNING
            ),
            AlertSeverity.INFO: (
                IncidentSeverity.INFO
            ),
        }

        return mapping[alert_severity]

    @staticmethod
    def _map_priority(
        alert_severity: AlertSeverity,
    ) -> IncidentPriority:
        """Map alert severity to operational priority."""

        mapping = {
            AlertSeverity.CRITICAL: (
                IncidentPriority.CRITICAL
            ),
            AlertSeverity.WARNING: (
                IncidentPriority.HIGH
            ),
            AlertSeverity.INFO: (
                IncidentPriority.LOW
            ),
        }

        return mapping[alert_severity]

    @staticmethod
    def _normalize_tag(
        value: str,
    ) -> str:
        """Normalize an enum value for incident tags."""

        return (
            value.strip()
            .lower()
            .replace("_", "-")
        )

    @staticmethod
    def _record_failure(
        db: Session,
        *,
        correlation,
        exc: Exception,
    ) -> None:
        """Persist a bounded application failure description."""

        failure_reason = (
            f"{type(exc).__name__}: {exc}"
        )

        IncidentCorrelationRepository.mark_failed(
            db=db,
            correlation=correlation,
            failure_reason=failure_reason[:10_000],
        )