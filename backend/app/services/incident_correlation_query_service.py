"""Read operations for persisted correlation decisions."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.correlation import (
    CorrelationApplicationStatus,
    CorrelationOutcome,
    CorrelationSignalFamily,
)
from app.models.incident_correlation import (
    IncidentCorrelation,
)
from app.repositories.incident_correlation_repository import (
    IncidentCorrelationRepository,
)


class IncidentCorrelationNotFoundError(
    LookupError
):
    """Raised when a persisted correlation does not exist."""

    def __init__(
        self,
        correlation_id: int,
    ) -> None:
        super().__init__(
            "incident correlation "
            f"{correlation_id} was not found"
        )

        self.correlation_id = correlation_id


class IncidentCorrelationQueryService:
    """Coordinate read-only correlation operations."""

    @staticmethod
    def get_required(
        db: Session,
        *,
        correlation_id: int,
    ) -> IncidentCorrelation:
        """Return a correlation or raise a domain error."""

        correlation = (
            IncidentCorrelationRepository.get_by_id(
                db=db,
                correlation_id=correlation_id,
            )
        )

        if correlation is None:
            raise IncidentCorrelationNotFoundError(
                correlation_id
            )

        return correlation

    @staticmethod
    def list_correlations(
        db: Session,
        *,
        source_alert_id: int | None = None,
        target_incident_id: int | None = None,
        outcome: CorrelationOutcome | None = None,
        application_status: (
            CorrelationApplicationStatus | None
        ) = None,
        signal_family: (
            CorrelationSignalFamily | None
        ) = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, object]:
        """Return filtered, paginated correlation history."""

        return (
            IncidentCorrelationRepository
            .get_paginated(
                db=db,
                source_alert_id=source_alert_id,
                target_incident_id=(
                    target_incident_id
                ),
                outcome=outcome,
                application_status=(
                    application_status
                ),
                signal_family=signal_family,
                page=page,
                page_size=page_size,
            )
        )