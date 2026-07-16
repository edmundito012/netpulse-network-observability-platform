"""High-level Incident Engine command orchestration."""

from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.schemas.incident import (
    IncidentAlertAttachRequest,
    IncidentCreate,
    IncidentResolveRequest,
    IncidentUpdate,
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
        )