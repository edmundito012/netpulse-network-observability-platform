"""Application service for incident portfolio evidence."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.incident import (
    Incident,
    IncidentStatus,
)
from app.repositories.incident_portfolio_repository import (
    IncidentPortfolioRepository,
)
from app.schemas.incident_portfolio import (
    IncidentPortfolioItem,
    IncidentPortfolioSummary,
)


class IncidentPortfolioService:
    """Build the public Incident Operations dashboard data."""

    @classmethod
    def get_summary(
        cls,
        db: Session,
        *,
        now: datetime | None = None,
    ) -> IncidentPortfolioSummary:
        """Return current incident aggregates and recent activity."""

        effective_now = (
            now
            or datetime.now(UTC)
        )

        latest = (
            IncidentPortfolioRepository
            .get_latest(
                db=db,
                limit=6,
            )
        )

        return IncidentPortfolioSummary(
            total_incidents=(
                IncidentPortfolioRepository
                .count_all(db)
            ),
            active_incidents=(
                IncidentPortfolioRepository
                .count_active(db)
            ),
            critical_incidents=(
                IncidentPortfolioRepository
                .count_active_critical(db)
            ),
            open_incidents=(
                IncidentPortfolioRepository
                .count_by_status(
                    db=db,
                    status=IncidentStatus.OPEN,
                )
            ),
            acknowledged_incidents=(
                IncidentPortfolioRepository
                .count_by_status(
                    db=db,
                    status=(
                        IncidentStatus.ACKNOWLEDGED
                    ),
                )
            ),
            investigating_incidents=(
                IncidentPortfolioRepository
                .count_by_status(
                    db=db,
                    status=(
                        IncidentStatus.INVESTIGATING
                    ),
                )
            ),
            monitoring_incidents=(
                IncidentPortfolioRepository
                .count_by_status(
                    db=db,
                    status=(
                        IncidentStatus.MONITORING
                    ),
                )
            ),
            resolved_incidents=(
                IncidentPortfolioRepository
                .count_by_status(
                    db=db,
                    status=IncidentStatus.RESOLVED,
                )
            ),
            correlated_alerts=(
                IncidentPortfolioRepository
                .count_correlated_alerts(db)
            ),
            affected_devices=(
                IncidentPortfolioRepository
                .count_affected_devices(db)
            ),
            mean_resolution_seconds=(
                IncidentPortfolioRepository
                .get_mean_resolution_seconds(db)
            ),
            latest_incidents=[
                cls._to_item(
                    incident=incident,
                    now=effective_now,
                )
                for incident in latest
            ],
        )

    @staticmethod
    def _to_item(
        *,
        incident: Incident,
        now: datetime,
    ) -> IncidentPortfolioItem:
        """Transform one incident into a dashboard item."""

        end_at = (
            incident.resolved_at
            or now
        )

        duration_seconds = max(
            0.0,
            (
                end_at
                - incident.started_at
            ).total_seconds(),
        )

        return IncidentPortfolioItem(
            public_id=incident.public_id,
            title=incident.title,
            status=incident.status,
            severity=incident.severity,
            priority=incident.priority,
            source=incident.source,
            alert_count=len(
                incident.alert_links
            ),
            started_at=incident.started_at,
            detected_at=incident.detected_at,
            duration_seconds=round(
                duration_seconds,
                2,
            ),
        )