"""Background processing for automatic alert correlation."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.correlation import (
    CorrelationConfiguration,
)
from app.core.logging import logger
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

        effective_configuration = (
            configuration
            or CorrelationConfiguration()
        )

        alert_ids = (
            CorrelationWorkerRepository
            .get_pending_alert_ids(
                db=db,
                limit=batch_size,
            )
        )

        processed = 0
        applied = 0
        replayed = 0
        failed_alert_ids: list[int] = []

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

                if result.replayed:
                    replayed += 1
                else:
                    applied += 1

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

            except Exception:
                db.rollback()

                failed_alert_ids.append(
                    alert_id
                )

                logger.exception(
                    "Correlation worker failed for alert=%s",
                    alert_id,
                )

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