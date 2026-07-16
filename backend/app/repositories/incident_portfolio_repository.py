"""Read-only persistence queries for the incident portfolio dashboard."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.alert import Alert
from app.models.incident import (
    Incident,
    IncidentStatus,
)
from app.models.incident_alert import IncidentAlert


class IncidentPortfolioRepository:
    """Retrieve aggregate incident information for portfolio evidence."""

    ACTIVE_STATUSES = (
        IncidentStatus.OPEN,
        IncidentStatus.ACKNOWLEDGED,
        IncidentStatus.INVESTIGATING,
        IncidentStatus.MONITORING,
    )

    @staticmethod
    def count_all(
        db: Session,
    ) -> int:
        """Return the total number of incidents."""

        statement = select(
            func.count(Incident.id)
        )

        return int(
            db.scalar(statement)
            or 0
        )

    @staticmethod
    def count_by_status(
        db: Session,
        *,
        status: IncidentStatus,
    ) -> int:
        """Return incidents in one lifecycle state."""

        statement = select(
            func.count(Incident.id)
        ).where(
            Incident.status == status
        )

        return int(
            db.scalar(statement)
            or 0
        )

    @classmethod
    def count_active(
        cls,
        db: Session,
    ) -> int:
        """Return incidents that are not resolved."""

        statement = select(
            func.count(Incident.id)
        ).where(
            Incident.status.in_(
                cls.ACTIVE_STATUSES
            )
        )

        return int(
            db.scalar(statement)
            or 0
        )

    @classmethod
    def count_active_critical(
        cls,
        db: Session,
    ) -> int:
        """Return active critical incidents."""

        from app.models.incident import (
            IncidentSeverity,
        )

        statement = select(
            func.count(Incident.id)
        ).where(
            Incident.status.in_(
                cls.ACTIVE_STATUSES
            ),
            Incident.severity
            == IncidentSeverity.CRITICAL,
        )

        return int(
            db.scalar(statement)
            or 0
        )

    @classmethod
    def count_correlated_alerts(
        cls,
        db: Session,
    ) -> int:
        """Return alerts attached to active incidents."""

        statement = (
            select(
                func.count(
                    IncidentAlert.id
                )
            )
            .select_from(IncidentAlert)
            .join(
                Incident,
                Incident.id
                == IncidentAlert.incident_id,
            )
            .where(
                Incident.status.in_(
                    cls.ACTIVE_STATUSES
                )
            )
        )

        return int(
            db.scalar(statement)
            or 0
        )

    @classmethod
    def count_affected_devices(
        cls,
        db: Session,
    ) -> int:
        """Return distinct devices represented by active incidents."""

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
                Incident,
                Incident.id
                == IncidentAlert.incident_id,
            )
            .join(
                Alert,
                Alert.id
                == IncidentAlert.alert_id,
            )
            .where(
                Incident.status.in_(
                    cls.ACTIVE_STATUSES
                )
            )
        )

        return int(
            db.scalar(statement)
            or 0
        )

    @staticmethod
    def get_mean_resolution_seconds(
        db: Session,
    ) -> float | None:
        """Return the average duration of resolved incidents."""

        statement = select(
            func.avg(
                func.extract(
                    "epoch",
                    Incident.resolved_at
                    - Incident.started_at,
                )
            )
        ).where(
            Incident.status
            == IncidentStatus.RESOLVED,
            Incident.resolved_at.is_not(None),
        )

        value = db.scalar(statement)

        if value is None:
            return None

        return round(
            max(
                0.0,
                float(value),
            ),
            2,
        )

    @staticmethod
    def get_latest(
        db: Session,
        *,
        limit: int = 6,
    ) -> list[Incident]:
        """Return the most recently detected incidents."""

        if limit < 1 or limit > 20:
            raise ValueError(
                "limit must be between 1 and 20"
            )

        statement = (
            select(Incident)
            .options(
                selectinload(
                    Incident.alert_links
                )
            )
            .order_by(
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