"""Read-only analytics queries for the Correlation Engine."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.orm import Session

from app.core.correlation import (
    CorrelationApplicationStatus,
    CorrelationOutcome,
)
from app.models.incident_correlation import (
    IncidentCorrelation,
)


class CorrelationAnalyticsRepository:
    """Aggregate persisted correlation decisions."""

    @staticmethod
    def get_totals(
        db: Session,
        *,
        window_started_at: datetime,
    ) -> dict[str, int | float | None]:
        """Return top-level correlation counters."""

        statement = select(
            func.count(
                IncidentCorrelation.id
            ).label(
                "total_evaluations"
            ),
            func.count(
                IncidentCorrelation.id
            ).filter(
                IncidentCorrelation.application_status
                == CorrelationApplicationStatus.APPLIED
            ).label(
                "applied_decisions"
            ),
            func.count(
                IncidentCorrelation.id
            ).filter(
                IncidentCorrelation.application_status
                == CorrelationApplicationStatus.FAILED
            ).label(
                "failed_decisions"
            ),
            func.count(
                IncidentCorrelation.id
            ).filter(
                IncidentCorrelation.application_status
                == CorrelationApplicationStatus.EVALUATED
            ).label(
                "pending_decisions"
            ),
            func.count(
                IncidentCorrelation.id
            ).filter(
                IncidentCorrelation.outcome
                == CorrelationOutcome.CREATE_NEW
            ).label(
                "incidents_created"
            ),
            func.count(
                IncidentCorrelation.id
            ).filter(
                IncidentCorrelation.outcome
                == CorrelationOutcome.MATCHED_EXISTING
            ).label(
                "existing_incidents_matched"
            ),
            func.count(
                IncidentCorrelation.id
            ).filter(
                IncidentCorrelation.outcome
                == CorrelationOutcome.NO_ACTION
            ).label(
                "no_action_decisions"
            ),
            func.avg(
                IncidentCorrelation.score
            ).label(
                "average_score"
            ),
        ).where(
            IncidentCorrelation.evaluated_at
            >= window_started_at
        )

        row = db.execute(
            statement
        ).one()

        return {
            "total_evaluations": int(
                row.total_evaluations or 0
            ),
            "applied_decisions": int(
                row.applied_decisions or 0
            ),
            "failed_decisions": int(
                row.failed_decisions or 0
            ),
            "pending_decisions": int(
                row.pending_decisions or 0
            ),
            "incidents_created": int(
                row.incidents_created or 0
            ),
            "existing_incidents_matched": int(
                row.existing_incidents_matched
                or 0
            ),
            "no_action_decisions": int(
                row.no_action_decisions or 0
            ),
            "average_score": (
                float(row.average_score)
                if row.average_score is not None
                else None
            ),
        }

    @staticmethod
    def count_by_column(
        db: Session,
        *,
        column,
        window_started_at: datetime,
    ) -> list[tuple[str, int]]:
        """Group correlation rows by an enum-like column."""

        statement = (
            select(
                column,
                func.count(
                    IncidentCorrelation.id
                ),
            )
            .where(
                IncidentCorrelation.evaluated_at
                >= window_started_at
            )
            .group_by(column)
            .order_by(
                func.count(
                    IncidentCorrelation.id
                ).desc(),
                column.asc(),
            )
        )

        rows = db.execute(
            statement
        ).all()

        return [
            (
                (
                    value.value
                    if hasattr(value, "value")
                    else str(value)
                ),
                int(count),
            )
            for value, count in rows
        ]

    @staticmethod
    def get_recent(
        db: Session,
        *,
        window_started_at: datetime,
        limit: int,
    ) -> list[IncidentCorrelation]:
        """Return the newest correlation decisions."""

        if limit < 1 or limit > 100:
            raise ValueError(
                "limit must be between 1 and 100"
            )

        statement = (
            select(IncidentCorrelation)
            .where(
                IncidentCorrelation.evaluated_at
                >= window_started_at
            )
            .order_by(
                IncidentCorrelation.evaluated_at.desc(),
                IncidentCorrelation.id.desc(),
            )
            .limit(limit)
        )

        return list(
            db.scalars(statement).all()
        )