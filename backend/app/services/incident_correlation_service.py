"""Application-independent orchestration for incident correlation."""

from __future__ import annotations

from hashlib import sha256

from sqlalchemy.orm import Session

from app.core.correlation import (
    CorrelationConfiguration,
    CorrelationOutcome,
    CorrelationReason,
)
from app.models.alert import Alert
from app.models.incident import Incident
from app.models.incident_correlation import (
    IncidentCorrelation,
)
from app.repositories.alert_repository import (
    AlertRepository,
)
from app.repositories.incident_correlation_repository import (
    IncidentCorrelationRepository,
)
from app.schemas.incident_correlation import (
    CorrelationCandidateRead,
    CorrelationEvaluationResult,
)
from app.schemas.incident_correlation_score import (
    CorrelationAlertSnapshot,
    CorrelationIncidentSnapshot,
    CorrelationScoreBreakdown,
)
from app.services.correlation_scoring_service import (
    CorrelationScoringService,
)
from app.services.correlation_signal_service import (
    CorrelationSignalService,
)


class SourceAlertNotFoundError(LookupError):
    """Raised when a requested source alert does not exist."""


class IncidentCorrelationService:
    """Evaluate alerts against active incident candidates."""

    @classmethod
    def evaluate(
        cls,
        db: Session,
        *,
        source_alert_id: int,
        configuration: (
            CorrelationConfiguration | None
        ) = None,
    ) -> CorrelationEvaluationResult:
        """Evaluate one alert without applying the decision."""

        config = (
            configuration
            or CorrelationConfiguration()
        )

        source_alert = AlertRepository.get_by_id(
            db=db,
            alert_id=source_alert_id,
        )

        if source_alert is None:
            raise SourceAlertNotFoundError(
                "source alert "
                f"{source_alert_id} was not found"
            )

        candidates = (
            IncidentCorrelationRepository
            .find_candidates(
                db=db,
                source_alert=source_alert,
                window_seconds=(
                    config.window_seconds
                ),
                limit=config.max_candidates,
            )
        )

        source_snapshot = (
            cls._build_alert_snapshot(
                source_alert
            )
        )

        scored_candidates = [
            CorrelationScoringService.score(
                alert=source_snapshot,
                incident=(
                    cls._build_incident_snapshot(
                        incident
                    )
                ),
                configuration=config,
            )
            for incident in candidates
        ]

        scored_candidates.sort(
            key=lambda candidate: (
                candidate.accepted,
                candidate.score,
                -candidate.time_distance_seconds,
                -candidate.incident_id,
            ),
            reverse=True,
        )

        best_candidate = (
            scored_candidates[0]
            if scored_candidates
            else None
        )

        accepted_candidate = (
            best_candidate
            if (
                best_candidate is not None
                and best_candidate.accepted
            )
            else None
        )

        signal_family = (
            CorrelationSignalService.classify(
                source_alert.alert_type
            )
        )

        if accepted_candidate is not None:
            outcome = (
                CorrelationOutcome.MATCHED_EXISTING
            )

            target_incident_id = (
                accepted_candidate.incident_id
            )

            target_public_id = (
                accepted_candidate
                .incident_public_id
            )

            score = accepted_candidate.score
            reasons = accepted_candidate.reasons

            explanation = (
                "Matched source alert "
                f"{source_alert.id} to incident "
                f"{target_public_id}. "
                f"{accepted_candidate.explanation}"
            )
        else:
            outcome = CorrelationOutcome.CREATE_NEW

            target_incident_id = None
            target_public_id = None

            score = (
                best_candidate.score
                if best_candidate is not None
                else 0.0
            )

            reasons = (
                list(best_candidate.reasons)
                if best_candidate is not None
                else [
                    CorrelationReason
                    .NO_CANDIDATE_INCIDENT
                ]
            )

            explanation = (
                cls._build_create_new_explanation(
                    source_alert=source_alert,
                    best_candidate=best_candidate,
                    candidate_count=len(
                        scored_candidates
                    ),
                    threshold=config.threshold,
                )
            )

        return CorrelationEvaluationResult(
            source_alert_id=source_alert.id,
            outcome=outcome,
            signal_family=signal_family,
            score=score,
            threshold=config.threshold,
            correlated=(
                accepted_candidate is not None
            ),
            target_incident_id=(
                target_incident_id
            ),
            target_incident_public_id=(
                target_public_id
            ),
            reasons=reasons,
            candidate_count=len(
                scored_candidates
            ),
            window_seconds=(
                config.window_seconds
            ),
            explanation=explanation,
            candidates=[
                cls._to_candidate_read(
                    candidate
                )
                for candidate
                in scored_candidates
            ],
        )

    @classmethod
    def evaluate_and_persist(
        cls,
        db: Session,
        *,
        source_alert_id: int,
        configuration: (
            CorrelationConfiguration | None
        ) = None,
    ) -> tuple[
        CorrelationEvaluationResult,
        IncidentCorrelation,
        bool,
    ]:
        """Evaluate and persist one idempotent decision."""

        config = (
            configuration
            or CorrelationConfiguration()
        )

        evaluation = cls.evaluate(
            db=db,
            source_alert_id=source_alert_id,
            configuration=config,
        )

        correlation_key = (
            cls.build_correlation_key(
                source_alert_id=source_alert_id,
                configuration=config,
            )
        )

        command = (
            IncidentCorrelationRepository
            .build_create_command(
                correlation_key=correlation_key,
                source_alert_id=(
                    evaluation.source_alert_id
                ),
                target_incident_id=(
                    evaluation.target_incident_id
                ),
                outcome=evaluation.outcome,
                signal_family=(
                    evaluation.signal_family
                ),
                score=evaluation.score,
                threshold=evaluation.threshold,
                reasons=evaluation.reasons,
                candidate_count=(
                    evaluation.candidate_count
                ),
                window_seconds=(
                    evaluation.window_seconds
                ),
                explanation=(
                    evaluation.explanation
                ),
                metadata={
                    "engine": (
                        "deterministic-correlation-v1"
                    ),
                    "max_candidates": (
                        config.max_candidates
                    ),
                    "candidate_scores": [
                        candidate.model_dump(
                            mode="json"
                        )
                        for candidate
                        in evaluation.candidates
                    ],
                },
            )
        )

        correlation, created = (
            IncidentCorrelationRepository
            .get_or_create(
                db=db,
                command=command,
            )
        )

        return (
            evaluation,
            correlation,
            created,
        )

    @staticmethod
    def build_correlation_key(
        *,
        source_alert_id: int,
        configuration: CorrelationConfiguration,
    ) -> str:
        """Build a stable key for an equivalent evaluation."""

        raw_key = (
            f"alert={source_alert_id};"
            f"window={configuration.window_seconds};"
            f"threshold={configuration.threshold:.6f};"
            f"max_candidates={configuration.max_candidates};"
            f"weights="
            f"{configuration.weights.same_device:.6f},"
            f"{configuration.weights.temporal_proximity:.6f},"
            f"{configuration.weights.signal_compatibility:.6f},"
            f"{configuration.weights.severity_alignment:.6f},"
            f"{configuration.weights.active_incident:.6f},"
            f"{configuration.weights.recent_detection:.6f}"
        )

        digest = sha256(
            raw_key.encode("utf-8")
        ).hexdigest()

        return (
            f"correlation:v1:"
            f"alert:{source_alert_id}:"
            f"{digest}"
        )

    @staticmethod
    def _build_alert_snapshot(
        alert: Alert,
    ) -> CorrelationAlertSnapshot:
        """Convert an Alert ORM model into scoring input."""

        observed_at = (
            alert.last_seen_at
            or alert.created_at
        )

        return CorrelationAlertSnapshot(
            id=alert.id,
            device_id=alert.device_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            observed_at=observed_at,
        )

    @staticmethod
    def _build_incident_snapshot(
        incident: Incident,
    ) -> CorrelationIncidentSnapshot:
        """Convert an Incident and its evidence into scoring input."""

        alerts = [
            link.alert
            for link in incident.alert_links
            if link.alert is not None
        ]

        if not alerts:
            raise ValueError(
                "candidate incidents must contain "
                "at least one alert"
            )

        latest_signal_at = max(
            (
                alert.last_seen_at
                or alert.created_at
            )
            for alert in alerts
        )

        return CorrelationIncidentSnapshot(
            id=incident.id,
            public_id=incident.public_id,
            status=incident.status,
            severity=incident.severity,
            detected_at=incident.detected_at,
            latest_signal_at=latest_signal_at,
            device_ids=frozenset(
                alert.device_id
                for alert in alerts
            ),
            alert_types=frozenset(
                alert.alert_type
                for alert in alerts
            ),
        )

    @staticmethod
    def _to_candidate_read(
        candidate: CorrelationScoreBreakdown,
    ) -> CorrelationCandidateRead:
        """Convert an internal breakdown to public candidate data."""

        return CorrelationCandidateRead(
            incident_id=candidate.incident_id,
            public_id=(
                candidate.incident_public_id
            ),
            score=candidate.score,
            reasons=candidate.reasons,
            time_distance_seconds=(
                candidate.time_distance_seconds
            ),
            is_active=not (
                CorrelationReason
                .INCIDENT_ALREADY_RESOLVED
                in candidate.reasons
            ),
        )

    @staticmethod
    def _build_create_new_explanation(
        *,
        source_alert: Alert,
        best_candidate: (
            CorrelationScoreBreakdown | None
        ),
        candidate_count: int,
        threshold: float,
    ) -> str:
        """Explain why the engine recommends a new incident."""

        if best_candidate is None:
            return (
                "No active incident candidate contained "
                "recent evidence for source alert "
                f"{source_alert.id}; create a new incident."
            )

        reason_text = ", ".join(
            reason.value
            for reason in best_candidate.reasons
        )

        return (
            "No candidate reached the correlation "
            f"threshold for source alert {source_alert.id}; "
            f"best_score={best_candidate.score:.4f}; "
            f"threshold={threshold:.4f}; "
            f"candidate_count={candidate_count}; "
            f"reasons=[{reason_text}]. "
            "Create a new incident."
        )