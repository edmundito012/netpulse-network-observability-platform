"""Persistence operations for the Correlation Engine."""

from __future__ import annotations

from datetime import (
    UTC,
    datetime,
    timedelta,
)
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.orm import (
    Session,
    joinedload,
    selectinload,
)

from app.core.correlation import (
    CorrelationApplicationStatus,
    CorrelationOutcome,
    CorrelationReason,
    CorrelationSignalFamily,
)
from app.models.alert import Alert
from app.models.incident import (
    Incident,
    IncidentStatus,
)
from app.models.incident_alert import IncidentAlert
from app.models.incident_correlation import (
    IncidentCorrelation,
)
from app.schemas.incident_correlation import (
    IncidentCorrelationCreate,
)


class IncidentCorrelationRepository:
    """Repository responsible for correlation persistence."""

    ACTIVE_INCIDENT_STATUSES = (
        IncidentStatus.OPEN,
        IncidentStatus.ACKNOWLEDGED,
        IncidentStatus.INVESTIGATING,
        IncidentStatus.MONITORING,
    )

    @staticmethod
    def get_by_id(
        db: Session,
        correlation_id: int,
    ) -> IncidentCorrelation | None:
        """Return a persisted correlation by ID."""

        statement = (
            select(IncidentCorrelation)
            .where(
                IncidentCorrelation.id
                == correlation_id
            )
            .options(
                joinedload(
                    IncidentCorrelation.source_alert
                ),
                joinedload(
                    IncidentCorrelation.target_incident
                ),
            )
        )

        return db.scalar(statement)

    @staticmethod
    def get_by_key(
        db: Session,
        correlation_key: str,
    ) -> IncidentCorrelation | None:
        """Return a persisted correlation by idempotency key."""

        statement = (
            select(IncidentCorrelation)
            .where(
                IncidentCorrelation.correlation_key
                == correlation_key
            )
            .options(
                joinedload(
                    IncidentCorrelation.source_alert
                ),
                joinedload(
                    IncidentCorrelation.target_incident
                ),
            )
        )

        return db.scalar(statement)

    @staticmethod
    def get_latest_for_alert(
        db: Session,
        *,
        source_alert_id: int,
    ) -> IncidentCorrelation | None:
        """Return the latest evaluation for one source alert."""

        statement = (
            select(IncidentCorrelation)
            .where(
                IncidentCorrelation.source_alert_id
                == source_alert_id
            )
            .options(
                joinedload(
                    IncidentCorrelation.source_alert
                ),
                joinedload(
                    IncidentCorrelation.target_incident
                ),
            )
            .order_by(
                IncidentCorrelation.evaluated_at.desc(),
                IncidentCorrelation.id.desc(),
            )
            .limit(1)
        )

        return db.scalar(statement)

    @staticmethod
    def create(
        db: Session,
        *,
        command: IncidentCorrelationCreate,
    ) -> IncidentCorrelation:
        """Persist an explainable correlation decision."""

        correlation = IncidentCorrelation(
            correlation_key=command.correlation_key,
            source_alert_id=command.source_alert_id,
            target_incident_id=(
                command.target_incident_id
            ),
            outcome=command.outcome,
            application_status=(
                command.application_status
            ),
            signal_family=command.signal_family,
            score=command.score,
            threshold=command.threshold,
            reasons=[
                reason.value
                for reason in command.reasons
            ],
            candidate_count=command.candidate_count,
            window_seconds=command.window_seconds,
            explanation=command.explanation,
            correlation_metadata=dict(
                command.metadata
            ),
            failure_reason=command.failure_reason,
            evaluated_at=(
                command.evaluated_at
                or datetime.now(UTC)
            ),
            applied_at=command.applied_at,
        )

        db.add(correlation)
        db.commit()
        db.refresh(correlation)

        return correlation

    @classmethod
    def get_or_create(
        cls,
        db: Session,
        *,
        command: IncidentCorrelationCreate,
    ) -> tuple[IncidentCorrelation, bool]:
        """Persist once using the deterministic correlation key."""

        existing = cls.get_by_key(
            db=db,
            correlation_key=command.correlation_key,
        )

        if existing is not None:
            return existing, False

        created = cls.create(
            db=db,
            command=command,
        )

        return created, True

    @classmethod
    def find_candidates(
        cls,
        db: Session,
        *,
        source_alert: Alert,
        window_seconds: int,
        limit: int,
    ) -> list[Incident]:
        """Return active incidents with recent evidence on the device."""

        if window_seconds < 60:
            raise ValueError(
                "window_seconds must be at least 60"
            )

        if limit < 1 or limit > 100:
            raise ValueError(
                "limit must be between 1 and 100"
            )

        observed_at = (
            source_alert.last_seen_at
            or source_alert.created_at
            or datetime.now(UTC)
        )

        window_start = (
            observed_at
            - timedelta(
                seconds=window_seconds,
            )
        )

        window_end = (
            observed_at
            + timedelta(
                seconds=window_seconds,
            )
        )

        candidate_ids_statement = (
            select(
                IncidentAlert.incident_id
            )
            .join(
                Alert,
                Alert.id
                == IncidentAlert.alert_id,
            )
            .join(
                Incident,
                Incident.id
                == IncidentAlert.incident_id,
            )
            .where(
                Incident.status.in_(
                    cls.ACTIVE_INCIDENT_STATUSES
                ),
                Alert.device_id
                == source_alert.device_id,
                Alert.last_seen_at >= window_start,
                Alert.last_seen_at <= window_end,
                Alert.id != source_alert.id,
            )
            .group_by(
                IncidentAlert.incident_id
            )
            .order_by(
                func.max(
                    Alert.last_seen_at
                ).desc(),
                IncidentAlert.incident_id.desc(),
            )
            .limit(limit)
        )

        candidate_ids = list(
            db.scalars(
                candidate_ids_statement
            ).all()
        )

        if not candidate_ids:
            return []

        statement = (
            select(Incident)
            .where(
                Incident.id.in_(
                    candidate_ids
                )
            )
            .options(
                selectinload(
                    Incident.alert_links
                ).joinedload(
                    IncidentAlert.alert
                )
            )
        )

        incidents = list(
            db.scalars(statement)
            .unique()
            .all()
        )

        incident_order = {
            incident_id: position
            for position, incident_id
            in enumerate(candidate_ids)
        }

        incidents.sort(
            key=lambda incident: (
                incident_order[
                    incident.id
                ]
            )
        )

        return incidents

    @staticmethod
    def get_paginated(
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
        """Return filtered correlation history."""

        if page < 1:
            raise ValueError(
                "page must be greater than or equal to 1"
            )

        if page_size < 1 or page_size > 100:
            raise ValueError(
                "page_size must be between 1 and 100"
            )

        filters: list[Any] = []

        if source_alert_id is not None:
            filters.append(
                IncidentCorrelation.source_alert_id
                == source_alert_id
            )

        if target_incident_id is not None:
            filters.append(
                IncidentCorrelation.target_incident_id
                == target_incident_id
            )

        if outcome is not None:
            filters.append(
                IncidentCorrelation.outcome
                == outcome
            )

        if application_status is not None:
            filters.append(
                IncidentCorrelation.application_status
                == application_status
            )

        if signal_family is not None:
            filters.append(
                IncidentCorrelation.signal_family
                == signal_family
            )

        count_statement = (
            select(
                func.count(
                    IncidentCorrelation.id
                )
            )
            .where(*filters)
        )

        total_count = (
            db.scalar(count_statement)
            or 0
        )

        statement = (
            select(IncidentCorrelation)
            .where(*filters)
            .options(
                joinedload(
                    IncidentCorrelation.source_alert
                ),
                joinedload(
                    IncidentCorrelation.target_incident
                ),
            )
            .order_by(
                IncidentCorrelation.evaluated_at.desc(),
                IncidentCorrelation.id.desc(),
            )
            .offset(
                (page - 1) * page_size
            )
            .limit(page_size)
        )

        items = list(
            db.scalars(statement)
            .unique()
            .all()
        )

        total_pages = (
            (
                total_count
                + page_size
                - 1
            )
            // page_size
            if total_count > 0
            else 0
        )

        return {
            "items": items,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    @staticmethod
    def mark_applied(
        db: Session,
        *,
        correlation: IncidentCorrelation,
        applied_incident_id: int | None = None,
        applied_incident_public_id: str | None = None,
        incident_created: bool = False,
        alert_attached: bool = False,
        applied_at: datetime | None = None,
    ) -> IncidentCorrelation:
        """Mark a correlation decision as successfully applied."""

        metadata = dict(
            correlation.correlation_metadata or {}
        )

        metadata.update(
            {
                "applied_incident_id": (
                    applied_incident_id
                ),
                "applied_incident_public_id": (
                    applied_incident_public_id
                ),
                "incident_created": (
                    incident_created
                ),
                "alert_attached": (
                    alert_attached
                ),
            }
        )

        correlation.application_status = (
            CorrelationApplicationStatus.APPLIED
        )

        correlation.applied_at = (
            applied_at
            or datetime.now(UTC)
        )

        correlation.failure_reason = None

        correlation.correlation_metadata = metadata

        db.commit()
        db.refresh(correlation)

        return correlation

    @staticmethod
    def mark_failed(
        db: Session,
        *,
        correlation: IncidentCorrelation,
        failure_reason: str,
    ) -> IncidentCorrelation:
        """Mark application of a decision as failed."""

        normalized_reason = failure_reason.strip()

        if not normalized_reason:
            raise ValueError(
                "failure_reason must not be empty"
            )

        metadata = dict(
            correlation.correlation_metadata or {}
        )

        metadata["application_failure"] = (
            normalized_reason
        )

        correlation.application_status = (
            CorrelationApplicationStatus.FAILED
        )

        correlation.failure_reason = (
            normalized_reason
        )

        correlation.applied_at = None
        correlation.correlation_metadata = metadata

        db.commit()
        db.refresh(correlation)

        return correlation

    @staticmethod
    def build_create_command(
        *,
        correlation_key: str,
        source_alert_id: int,
        target_incident_id: int | None,
        outcome: CorrelationOutcome,
        signal_family: CorrelationSignalFamily,
        score: float,
        threshold: float,
        reasons: list[CorrelationReason],
        candidate_count: int,
        window_seconds: int,
        explanation: str,
        metadata: dict[str, Any] | None = None,
    ) -> IncidentCorrelationCreate:
        """Build a validated persistence command."""

        return IncidentCorrelationCreate(
            correlation_key=correlation_key,
            source_alert_id=source_alert_id,
            target_incident_id=target_incident_id,
            outcome=outcome,
            application_status=(
                CorrelationApplicationStatus.EVALUATED
            ),
            signal_family=signal_family,
            score=Decimal(
                f"{score:.4f}"
            ),
            threshold=Decimal(
                f"{threshold:.4f}"
            ),
            reasons=reasons,
            candidate_count=candidate_count,
            window_seconds=window_seconds,
            explanation=explanation,
            metadata=dict(
                metadata or {}
            ),
            evaluated_at=datetime.now(UTC),
        )