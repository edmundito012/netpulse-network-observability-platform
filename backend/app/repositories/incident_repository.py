"""Persistence operations for the Incident Engine."""

from __future__ import annotations

from datetime import UTC, datetime
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

from app.models.incident import (
    Incident,
    IncidentPriority,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)
from app.models.incident_alert import IncidentAlert


class IncidentRepository:
    """Repository responsible for incident persistence."""

    ACTIVE_STATUSES = (
        IncidentStatus.OPEN,
        IncidentStatus.ACKNOWLEDGED,
        IncidentStatus.INVESTIGATING,
        IncidentStatus.MONITORING,
    )

    @staticmethod
    def create(
        db: Session,
        *,
        title: str,
        description: str | None = None,
        severity: IncidentSeverity = (
            IncidentSeverity.WARNING
        ),
        priority: IncidentPriority = (
            IncidentPriority.MEDIUM
        ),
        source: IncidentSource = (
            IncidentSource.MANUAL
        ),
        owner_id: int | None = None,
        business_impact: str | None = None,
        started_at: datetime | None = None,
        tags: list[str] | None = None,
        incident_metadata: dict[str, Any] | None = None,
    ) -> Incident:
        """Persist a new operational incident."""

        now = datetime.now(UTC)

        incident = Incident(
            title=title,
            description=description,
            status=IncidentStatus.OPEN,
            severity=severity,
            priority=priority,
            source=source,
            owner_id=owner_id,
            business_impact=business_impact,
            started_at=started_at or now,
            detected_at=now,
            tags=list(tags or []),
            incident_metadata=dict(
                incident_metadata or {}
            ),
        )

        db.add(incident)
        db.commit()
        db.refresh(incident)

        return incident

    @classmethod
    def get_by_id(
        cls,
        db: Session,
        incident_id: int,
        *,
        include_alerts: bool = True,
    ) -> Incident | None:
        """Return an incident by its internal database ID."""

        statement = select(Incident).where(
            Incident.id == incident_id
        )

        if include_alerts:
            statement = cls._with_alerts(
                statement
            )

        return db.scalar(statement)

    @classmethod
    def get_by_public_id(
        cls,
        db: Session,
        public_id: str,
        *,
        include_alerts: bool = True,
    ) -> Incident | None:
        """Return an incident by its public identifier."""

        statement = select(Incident).where(
            Incident.public_id == public_id
        )

        if include_alerts:
            statement = cls._with_alerts(
                statement
            )

        return db.scalar(statement)

    @classmethod
    def get_paginated(
        cls,
        db: Session,
        *,
        status: IncidentStatus | None = None,
        severity: IncidentSeverity | None = None,
        priority: IncidentPriority | None = None,
        source: IncidentSource | None = None,
        owner_id: int | None = None,
        active_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, object]:
        """Return filtered incidents with pagination metadata."""

        cls._validate_pagination(
            page=page,
            page_size=page_size,
        )

        filters = cls._build_filters(
            status=status,
            severity=severity,
            priority=priority,
            source=source,
            owner_id=owner_id,
            active_only=active_only,
        )

        count_statement = (
            select(
                func.count(Incident.id)
            )
            .where(*filters)
        )

        total_count = (
            db.scalar(count_statement)
            or 0
        )

        statement = (
            select(Incident)
            .where(*filters)
            .options(
                selectinload(
                    Incident.alert_links
                )
            )
            .order_by(
                Incident.detected_at.desc(),
                Incident.id.desc(),
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

    @classmethod
    def get_active_incidents(
        cls,
        db: Session,
        *,
        limit: int = 100,
    ) -> list[Incident]:
        """Return operational incidents that are not resolved."""

        if limit < 1 or limit > 10_000:
            raise ValueError(
                "limit must be between 1 and 10000"
            )

        statement = (
            select(Incident)
            .where(
                Incident.status.in_(
                    cls.ACTIVE_STATUSES
                )
            )
            .options(
                selectinload(
                    Incident.alert_links
                )
            )
            .order_by(
                Incident.severity.desc(),
                Incident.detected_at.desc(),
                Incident.id.desc(),
            )
            .limit(limit)
        )

        return list(
            db.scalars(statement)
            .unique()
            .all()
        )

    @staticmethod
    def update_details(
        db: Session,
        *,
        incident: Incident,
        title: str | None = None,
        description: str | None = None,
        severity: IncidentSeverity | None = None,
        priority: IncidentPriority | None = None,
        business_impact: str | None = None,
        root_cause: str | None = None,
        tags: list[str] | None = None,
        incident_metadata: dict[str, Any] | None = None,
    ) -> Incident:
        """Persist editable incident details.

        Lifecycle state changes are intentionally excluded and will be
        handled by IncidentLifecycleService.
        """

        if title is not None:
            incident.title = title

        if description is not None:
            incident.description = description

        if severity is not None:
            incident.severity = severity

        if priority is not None:
            incident.priority = priority

        if business_impact is not None:
            incident.business_impact = business_impact

        if root_cause is not None:
            incident.root_cause = root_cause

        if tags is not None:
            incident.tags = list(tags)

        if incident_metadata is not None:
            incident.incident_metadata = dict(
                incident_metadata
            )

        incident.updated_at = datetime.now(UTC)

        db.commit()
        db.refresh(incident)

        return incident

    @staticmethod
    def assign_owner(
        db: Session,
        *,
        incident: Incident,
        owner_id: int | None,
    ) -> Incident:
        """Assign or remove an incident owner."""

        incident.owner_id = owner_id
        incident.updated_at = datetime.now(UTC)

        db.commit()
        db.refresh(incident)

        return incident

    @staticmethod
    def get_alert_link(
        db: Session,
        *,
        alert_id: int,
    ) -> IncidentAlert | None:
        """Return the current incident association for an alert."""

        statement = (
            select(IncidentAlert)
            .where(
                IncidentAlert.alert_id == alert_id
            )
            .options(
                joinedload(
                    IncidentAlert.incident
                ),
                joinedload(
                    IncidentAlert.alert
                ),
            )
        )

        return db.scalar(statement)

    @staticmethod
    def attach_alert(
        db: Session,
        *,
        incident_id: int,
        alert_id: int,
    ) -> IncidentAlert:
        """Attach an alert to an incident.

        Callers should check ``get_alert_link`` first when they need to
        distinguish idempotency from a conflict with another incident.
        The database unique constraint remains the final concurrency
        safeguard.
        """

        link = IncidentAlert(
            incident_id=incident_id,
            alert_id=alert_id,
        )

        db.add(link)
        db.commit()
        db.refresh(link)

        return link

    @staticmethod
    def detach_alert(
        db: Session,
        *,
        incident_id: int,
        alert_id: int,
    ) -> bool:
        """Detach an alert from an incident.

        Returns ``True`` when an association existed and was removed.
        """

        statement = select(
            IncidentAlert
        ).where(
            IncidentAlert.incident_id
            == incident_id,
            IncidentAlert.alert_id
            == alert_id,
        )

        link = db.scalar(statement)

        if link is None:
            return False

        db.delete(link)
        db.commit()

        return True

    @staticmethod
    def count_alerts(
        db: Session,
        *,
        incident_id: int,
    ) -> int:
        """Return the number of alerts attached to an incident."""

        statement = (
            select(
                func.count(
                    IncidentAlert.id
                )
            )
            .where(
                IncidentAlert.incident_id
                == incident_id
            )
        )

        return db.scalar(statement) or 0

    @staticmethod
    def get_affected_device_count(
        db: Session,
        *,
        incident_id: int,
    ) -> int:
        """Return the number of distinct devices represented by alerts."""

        from app.models.alert import Alert

        statement = (
            select(
                func.count(
                    func.distinct(
                        Alert.device_id
                    )
                )
            )
            .select_from(IncidentAlert)
            .join(
                Alert,
                Alert.id
                == IncidentAlert.alert_id,
            )
            .where(
                IncidentAlert.incident_id
                == incident_id
            )
        )

        return db.scalar(statement) or 0

    @staticmethod
    def _build_filters(
        *,
        status: IncidentStatus | None,
        severity: IncidentSeverity | None,
        priority: IncidentPriority | None,
        source: IncidentSource | None,
        owner_id: int | None,
        active_only: bool,
    ) -> list[object]:
        filters: list[object] = []

        if active_only:
            filters.append(
                Incident.status.in_(
                    IncidentRepository
                    .ACTIVE_STATUSES
                )
            )
        elif status is not None:
            filters.append(
                Incident.status == status
            )

        if severity is not None:
            filters.append(
                Incident.severity
                == severity
            )

        if priority is not None:
            filters.append(
                Incident.priority
                == priority
            )

        if source is not None:
            filters.append(
                Incident.source
                == source
            )

        if owner_id is not None:
            filters.append(
                Incident.owner_id
                == owner_id
            )

        return filters

    @staticmethod
    def _validate_pagination(
        *,
        page: int,
        page_size: int,
    ) -> None:
        if page < 1:
            raise ValueError(
                "page must be greater than or equal to 1"
            )

        if page_size < 1 or page_size > 100:
            raise ValueError(
                "page_size must be between 1 and 100"
            )

    @staticmethod
    def _with_alerts(
        statement,
    ):
        return statement.options(
            selectinload(
                Incident.alert_links
            ).joinedload(
                IncidentAlert.alert
            )
        )