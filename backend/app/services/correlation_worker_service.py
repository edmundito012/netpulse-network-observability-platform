"""Background processing for automatic alert correlation."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from sqlalchemy.orm import Session

from app.core.correlation import (
    CorrelationConfiguration,
    CorrelationOutcome,
)
from app.core.logging import logger
from app.core.metrics import (
    correlation_applications_total,
    correlation_evaluations_total,
    correlation_existing_incidents_matched_total,
    correlation_failures_total,
    correlation_incidents_created_total,
    correlation_no_action_total,
    correlation_worker_duration_seconds,
    correlation_worker_pending_alerts,
    correlation_worker_processed_alerts_total,
    correlation_worker_runs_total,
)
from app.repositories.correlation_worker_repository import (
    CorrelationWorkerRepository,
)
from app.services.incident_correlation_application_service import (
    IncidentCorrelationApplicationService,
)


@dataclass(frozen=True, slots=True)
class CorrelationWorkerResult:
    """Summary of one worker execution."""

    discovered: int
    processed: int
    applied: int
    replayed: int
    failed: int

    failed_alert_ids: tuple[int, ...]


class CorrelationWorkerService:
    """Process alerts awaiting automatic correlation."""

    @classmethod
    def run_batch(
        cls,
        db: Session,
        *,
        batch_size: int = 25,
        configuration: (
            CorrelationConfiguration | None
        ) = None,
    ) -> CorrelationWorkerResult:
        """Evaluate and apply a bounded batch of pending alerts."""

        if batch_size < 1 or batch_size > 500:
            raise ValueError(
                "batch_size must be between 1 and 500"
            )

        started_at = perf_counter()

        effective_configuration = (
            configuration
            or CorrelationConfiguration()
        )

        alert_ids: list[int] = []
        processed = 0
        applied = 0
        replayed = 0
        failed_alert_ids: list[int] = []

        try:
            alert_ids = (
                CorrelationWorkerRepository
                .get_pending_alert_ids(
                    db=db,
                    limit=batch_size,
                )
            )

            correlation_worker_pending_alerts.set(
                len(alert_ids)
            )

            for alert_id in alert_ids:
                processed += 1

                try:
                    result = (
                        IncidentCorrelationApplicationService
                        .evaluate_and_apply(
                            db=db,
                            source_alert_id=alert_id,
                            configuration=(
                                effective_configuration
                            ),
                        )
                    )

                    cls._record_success_metrics(
                        result=result,
                    )

                    if result.replayed:
                        replayed += 1

                        correlation_worker_processed_alerts_total.labels(
                            status="replayed",
                        ).inc()
                    else:
                        applied += 1

                        correlation_worker_processed_alerts_total.labels(
                            status="applied",
                        ).inc()

                    logger.info(
                        "Correlation worker processed alert=%s "
                        "correlation=%s outcome=%s "
                        "incident=%s replayed=%s",
                        alert_id,
                        result.correlation_id,
                        result.outcome.value,
                        result.incident_id,
                        result.replayed,
                    )

                except Exception as exc:
                    db.rollback()

                    failed_alert_ids.append(
                        alert_id
                    )

                    correlation_worker_processed_alerts_total.labels(
                        status="failed",
                    ).inc()

                    correlation_failures_total.labels(
                        exception_type=(
                            type(exc).__name__
                        ),
                    ).inc()

                    logger.exception(
                        "Correlation worker failed for alert=%s",
                        alert_id,
                    )

            worker_status = cls._resolve_worker_status(
                discovered=len(alert_ids),
                failed=len(failed_alert_ids),
            )

            correlation_worker_runs_total.labels(
                status=worker_status,
            ).inc()

            return CorrelationWorkerResult(
                discovered=len(alert_ids),
                processed=processed,
                applied=applied,
                replayed=replayed,
                failed=len(failed_alert_ids),
                failed_alert_ids=tuple(
                    failed_alert_ids
                ),
            )

        except Exception as exc:
            correlation_worker_runs_total.labels(
                status="failed",
            ).inc()

            correlation_failures_total.labels(
                exception_type=type(exc).__name__,
            ).inc()

            raise

        finally:
            correlation_worker_duration_seconds.observe(
                perf_counter() - started_at
            )

    @staticmethod
    def _record_success_metrics(
        *,
        result,
    ) -> None:
        """Record metrics for one successfully evaluated alert."""

        outcome = result.outcome

        correlation_evaluations_total.labels(
            outcome=outcome.value,
        ).inc()

        application_status = (
            "replayed"
            if result.replayed
            else "applied"
        )

        correlation_applications_total.labels(
            status=application_status,
        ).inc()

        if result.replayed:
            return

        if result.incident_created:
            correlation_incidents_created_total.inc()

        if (
            outcome
            == CorrelationOutcome.MATCHED_EXISTING
        ):
            correlation_existing_incidents_matched_total.inc()

        if outcome == CorrelationOutcome.NO_ACTION:
            correlation_no_action_total.inc()

    @staticmethod
    def _resolve_worker_status(
        *,
        discovered: int,
        failed: int,
    ) -> str:
        """Return the operational result label for one batch."""

        if failed == 0:
            return "success"

        if discovered > failed:
            return "partial"

        return "failed"