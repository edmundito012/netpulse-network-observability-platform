"""Application service for Correlation Engine analytics."""

from __future__ import annotations

from datetime import (
    UTC,
    datetime,
    timedelta,
)

from sqlalchemy.orm import Session

from app.models.incident_correlation import (
    IncidentCorrelation,
)
from app.repositories.correlation_analytics_repository import (
    CorrelationAnalyticsRepository,
)
from app.schemas.correlation_analytics import (
    CorrelationAnalyticsCount,
    CorrelationAnalyticsRecentItem,
    CorrelationAnalyticsSummary,
)


class CorrelationAnalyticsService:
    """Build operator-facing correlation analytics."""

    @classmethod
    def get_summary(
        cls,
        db: Session,
        *,
        window_hours: int = 24,
        recent_limit: int = 20,
    ) -> CorrelationAnalyticsSummary:
        """Return analytics for the requested temporal window."""

        if window_hours < 1 or window_hours > 720:
            raise ValueError(
                "window_hours must be between 1 and 720"
            )

        if recent_limit < 1 or recent_limit > 100:
            raise ValueError(
                "recent_limit must be between 1 and 100"
            )

        generated_at = datetime.now(UTC)

        window_started_at = (
            generated_at
            - timedelta(
                hours=window_hours,
            )
        )

        totals = (
            CorrelationAnalyticsRepository
            .get_totals(
                db=db,
                window_started_at=window_started_at,
            )
        )

        total_evaluations = int(
            totals["total_evaluations"]
        )

        applied_decisions = int(
            totals["applied_decisions"]
        )

        failed_decisions = int(
            totals["failed_decisions"]
        )

        pending_decisions = int(
            totals["pending_decisions"]
        )

        incidents_created = int(
            totals["incidents_created"]
        )

        existing_incidents_matched = int(
            totals[
                "existing_incidents_matched"
            ]
        )

        successful_decisions = (
            applied_decisions
        )

        application_success_rate = (
            cls._percentage(
                successful_decisions,
                (
                    successful_decisions
                    + failed_decisions
                ),
            )
        )

        incident_reuse_rate = (
            cls._percentage(
                existing_incidents_matched,
                (
                    existing_incidents_matched
                    + incidents_created
                ),
            )
        )

        recent = (
            CorrelationAnalyticsRepository
            .get_recent(
                db=db,
                window_started_at=window_started_at,
                limit=recent_limit,
            )
        )

        return CorrelationAnalyticsSummary(
            window_hours=window_hours,
            window_started_at=window_started_at,
            generated_at=generated_at,
            total_evaluations=total_evaluations,
            applied_decisions=applied_decisions,
            failed_decisions=failed_decisions,
            pending_decisions=pending_decisions,
            incidents_created=incidents_created,
            existing_incidents_matched=(
                existing_incidents_matched
            ),
            no_action_decisions=int(
                totals["no_action_decisions"]
            ),
            successful_decisions=(
                successful_decisions
            ),
            average_score=(
                round(
                    float(totals["average_score"]),
                    4,
                )
                if totals["average_score"]
                is not None
                else None
            ),
            application_success_rate=(
                application_success_rate
            ),
            incident_reuse_rate=(
                incident_reuse_rate
            ),
            estimated_incidents_avoided=(
                existing_incidents_matched
            ),
            outcomes=cls._get_counts(
                db=db,
                column=(
                    IncidentCorrelation.outcome
                ),
                window_started_at=(
                    window_started_at
                ),
            ),
            application_statuses=cls._get_counts(
                db=db,
                column=(
                    IncidentCorrelation
                    .application_status
                ),
                window_started_at=(
                    window_started_at
                ),
            ),
            signal_families=cls._get_counts(
                db=db,
                column=(
                    IncidentCorrelation
                    .signal_family
                ),
                window_started_at=(
                    window_started_at
                ),
            ),
            recent_correlations=[
                cls._build_recent_item(
                    correlation
                )
                for correlation in recent
            ],
        )

    @staticmethod
    def _percentage(
        numerator: int,
        denominator: int,
    ) -> float:
        """Calculate a bounded percentage."""

        if denominator <= 0:
            return 0.0

        return round(
            (
                numerator
                / denominator
            )
            * 100.0,
            2,
        )

    @staticmethod
    def _get_counts(
        db: Session,
        *,
        column,
        window_started_at: datetime,
    ) -> list[CorrelationAnalyticsCount]:
        """Convert repository grouped counts into schemas."""

        rows = (
            CorrelationAnalyticsRepository
            .count_by_column(
                db=db,
                column=column,
                window_started_at=(
                    window_started_at
                ),
            )
        )

        return [
            CorrelationAnalyticsCount(
                name=name,
                count=count,
            )
            for name, count in rows
        ]

    @staticmethod
    def _build_recent_item(
        correlation: IncidentCorrelation,
    ) -> CorrelationAnalyticsRecentItem:
        """Convert one persisted decision into a compact item."""

        return CorrelationAnalyticsRecentItem(
            correlation_id=correlation.id,
            source_alert_id=(
                correlation.source_alert_id
            ),
            target_incident_id=(
                correlation.target_incident_id
            ),
            outcome=correlation.outcome.value,
            application_status=(
                correlation
                .application_status
                .value
            ),
            signal_family=(
                correlation.signal_family.value
            ),
            score=float(correlation.score),
            evaluated_at=(
                correlation.evaluated_at
            ),
        )