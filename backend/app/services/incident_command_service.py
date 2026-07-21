"""High-level Incident Engine command orchestration."""

from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.schemas.incident import (
    IncidentAlertAttachRequest,
    IncidentCreate,
    IncidentResolveRequest,
    IncidentUpdate,
)
from app.services.incident_actor_context import (
    IncidentActorContext,
)
from app.services.incident_lifecycle_service import (
    IncidentLifecycleService,
)
from app.services.incident_service import (
    IncidentService,
)


class IncidentCommandService:
    """Execute complete incident commands by public identifier."""

    @staticmethod
    def create(
        db: Session,
        *,
        incident_data: IncidentCreate,
    ) -> Incident:
        """Create an operational incident."""

        return IncidentService.create(
            db=db,
            incident_data=incident_data,
        )

    @staticmethod
    def update(
        db: Session,
        *,
        public_id: str,
        incident_data: IncidentUpdate,
        actor: IncidentActorContext,
    ) -> Incident:
        """Update editable incident information."""

        incident = (
            IncidentService
            .get_required_by_public_id(
                db=db,
                public_id=public_id,
            )
        )

        updated = IncidentService.update(
            db=db,
            incident=incident,
            incident_data=incident_data,
            actor_type=actor.actor_type,
            actor_id=actor.actor_id,
            actor_label=actor.actor_label,
        )

        return (
            IncidentService
            .get_required_by_public_id(
                db=db,
                public_id=updated.public_id,
            )
        )

    @staticmethod
    def acknowledge(
        db: Session,
        *,
        public_id: str,
        actor: IncidentActorContext,
    ) -> Incident:
        """Acknowledge an incident."""

        incident = (
            IncidentService
            .get_required_by_public_id(
                db=db,
                public_id=public_id,
            )
        )

        updated = (
            IncidentLifecycleService
            .acknowledge(
                db=db,
                incident=incident,
                actor_type=actor.actor_type,
                actor_id=actor.actor_id,
                actor_label=actor.actor_label,
            )
        )

        return (
            IncidentService
            .get_required_by_public_id(
                db=db,
                public_id=updated.public_id,
            )
        )

    @staticmethod
    def investigate(
        db: Session,
        *,
        public_id: str,
        actor: IncidentActorContext,
    ) -> Incident:
        """Start incident investigation."""

        incident = (
            IncidentService
            .get_required_by_public_id(
                db=db,
                public_id=public_id,
            )
        )

        updated = (
            IncidentLifecycleService
            .start_investigation(
                db=db,
                incident=incident,
                actor_type=actor.actor_type,
                actor_id=actor.actor_id,
                actor_label=actor.actor_label,
            )
        )

        return (
            IncidentService
            .get_required_by_public_id(
                db=db,
                public_id=updated.public_id,
            )
        )

    @staticmethod
    def monitor(
        db: Session,
        *,
        public_id: str,
        actor: IncidentActorContext,
    ) -> Incident:
        """Move an incident into monitoring."""

        incident = (
            IncidentService
            .get_required_by_public_id(
                db=db,
                public_id=public_id,
            )
        )

        updated = (
            IncidentLifecycleService
            .start_monitoring(
                db=db,
                incident=incident,
                actor_type=actor.actor_type,
                actor_id=actor.actor_id,
                actor_label=actor.actor_label,
            )
        )

        return (
            IncidentService
            .get_required_by_public_id(
                db=db,
                public_id=updated.public_id,
            )
        )

    @staticmethod
    def resolve(
        db: Session,
        *,
        public_id: str,
        resolution_data: IncidentResolveRequest,
        actor: IncidentActorContext,
    ) -> Incident:
        """Resolve an incident with operational context."""

        incident = (
            IncidentService
            .get_required_by_public_id(
                db=db,
                public_id=public_id,
            )
        )

        updated = (
            IncidentLifecycleService.resolve(
                db=db,
                incident=incident,
                resolution_summary=(
                    resolution_data
                    .resolution_summary
                ),
                root_cause=(
                    resolution_data.root_cause
                ),
                actor_type=actor.actor_type,
                actor_id=actor.actor_id,
                actor_label=actor.actor_label,
            )
        )

        return (
            IncidentService
            .get_required_by_public_id(
                db=db,
                public_id=updated.public_id,
            )
        )

    @staticmethod
    def attach_alerts(
        db: Session,
        *,
        public_id: str,
        attachment_data: (
            IncidentAlertAttachRequest
        ),
        actor: IncidentActorContext,
    ) -> Incident:
        """Attach multiple alerts to an incident."""

        incident = (
            IncidentService
            .get_required_by_public_id(
                db=db,
                public_id=public_id,
            )
        )

        for alert_id in attachment_data.alert_ids:
            IncidentService.attach_alert(
                db=db,
                incident=incident,
                alert_id=alert_id,
                actor_type=actor.actor_type,
                actor_id=actor.actor_id,
                actor_label=actor.actor_label,
            )

        return (
            IncidentService
            .get_required_by_public_id(
                db=db,
                public_id=public_id,
            )
        )

    @staticmethod
    def detach_alert(
        db: Session,
        *,
        public_id: str,
        alert_id: int,
        actor: IncidentActorContext,
    ) -> None:
        """Detach one alert from an incident."""

        incident = (
            IncidentService
            .get_required_by_public_id(
                db=db,
                public_id=public_id,
            )
        )

        IncidentService.detach_alert(
            db=db,
            incident=incident,
            alert_id=alert_id,
            actor_type=actor.actor_type,
            actor_id=actor.actor_id,
            actor_label=actor.actor_label,
        )