"""Persistence queries used by the correlation worker."""

from __future__ import annotations

from sqlalchemy import (
    exists,
    select,
)
from sqlalchemy.orm import Session

from app.models.alert import (
    Alert,
    AlertStatus,
)
from app.models.incident_correlation import (
    IncidentCorrelation,
)


class CorrelationWorkerRepository:
    """Find alerts awaiting their first correlation evaluation."""

    @staticmethod
    def get_pending_alert_ids(
        db: Session,
        *,
        limit: int,
    ) -> list[int]:
        """Return open alerts without a persisted correlation."""

        if limit < 1 or limit > 500:
            raise ValueError(
                "limit must be between 1 and 500"
            )

        correlation_exists = exists(
            select(IncidentCorrelation.id)
            .where(
                IncidentCorrelation.source_alert_id
                == Alert.id
            )
        )

        statement = (
            select(Alert.id)
            .where(
                Alert.status.in_(
                    (
                        AlertStatus.OPEN,
                        AlertStatus.ACKNOWLEDGED,
                    )
                ),
                ~correlation_exists,
            )
            .order_by(
                Alert.created_at.asc(),
                Alert.id.asc(),
            )
            .limit(limit)
        )

        return list(
            db.scalars(statement).all()
        )