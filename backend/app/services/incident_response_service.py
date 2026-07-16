"""Incident API response transformation service."""

from app.models.incident import Incident
from app.schemas.incident import (
    IncidentAlertRead,
    IncidentPaginationResponse,
    IncidentRead,
    IncidentStatisticsResponse,
    IncidentSummary,
)
from app.services.incident_service import (
    IncidentStatistics,
)


class IncidentResponseService:
    """Transform incident domain objects into API schemas."""

    @classmethod
    def to_read(
        cls,
        incident: Incident,
    ) -> IncidentRead:
        """Build a complete incident response."""

        alerts = [
            IncidentAlertRead(
                id=link.alert.id,
                device_id=link.alert.device_id,
                alert_type=link.alert.alert_type,
                severity=link.alert.severity,
                status=link.alert.status,
                message=link.alert.message,
                occurrence_count=(
                    link.alert.occurrence_count
                ),
                first_seen_at=(
                    link.alert.first_seen_at
                ),
                last_seen_at=(
                    link.alert.last_seen_at
                ),
                created_at=link.alert.created_at,
                resolved_at=link.alert.resolved_at,
                attached_at=link.attached_at,
            )
            for link in incident.alert_links
        ]

        return IncidentRead(
            id=incident.id,
            public_id=incident.public_id,
            title=incident.title,
            description=incident.description,
            status=incident.status,
            severity=incident.severity,
            priority=incident.priority,
            source=incident.source,
            owner_id=incident.owner_id,
            business_impact=(
                incident.business_impact
            ),
            root_cause=incident.root_cause,
            resolution_summary=(
                incident.resolution_summary
            ),
            tags=list(
                incident.tags or []
            ),
            metadata=dict(
                incident.incident_metadata or {}
            ),
            started_at=incident.started_at,
            detected_at=incident.detected_at,
            acknowledged_at=(
                incident.acknowledged_at
            ),
            resolved_at=incident.resolved_at,
            created_at=incident.created_at,
            updated_at=incident.updated_at,
            alerts=alerts,
        )

    @staticmethod
    def to_summary(
        incident: Incident,
    ) -> IncidentSummary:
        """Build a compact incident response."""

        return IncidentSummary(
            id=incident.id,
            public_id=incident.public_id,
            title=incident.title,
            status=incident.status,
            severity=incident.severity,
            priority=incident.priority,
            source=incident.source,
            owner_id=incident.owner_id,
            alert_count=len(
                incident.alert_links
            ),
            started_at=incident.started_at,
            detected_at=incident.detected_at,
            acknowledged_at=(
                incident.acknowledged_at
            ),
            resolved_at=incident.resolved_at,
            created_at=incident.created_at,
            updated_at=incident.updated_at,
        )

    @classmethod
    def to_paginated(
        cls,
        result: dict[str, object],
    ) -> IncidentPaginationResponse:
        """Transform a repository pagination result."""

        incidents = result["items"]

        return IncidentPaginationResponse(
            items=[
                cls.to_summary(incident)
                for incident in incidents
            ],
            total_count=int(
                result["total_count"]
            ),
            page=int(result["page"]),
            page_size=int(
                result["page_size"]
            ),
            total_pages=int(
                result["total_pages"]
            ),
        )

    @staticmethod
    def to_statistics(
        statistics: IncidentStatistics,
    ) -> IncidentStatisticsResponse:
        """Transform calculated incident statistics."""

        return IncidentStatisticsResponse(
            incident_id=statistics.incident_id,
            public_id=statistics.public_id,
            alert_count=statistics.alert_count,
            affected_device_count=(
                statistics.affected_device_count
            ),
            duration_seconds=(
                statistics.duration_seconds
            ),
            is_active=statistics.is_active,
        )