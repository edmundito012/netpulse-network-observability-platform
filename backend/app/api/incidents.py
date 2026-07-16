"""Incident Engine HTTP API."""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user,
    require_roles,
)
from app.db.session import get_db
from app.models.incident import (
    IncidentPriority,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)
from app.models.user import (
    User,
    UserRole,
)
from app.schemas.incident import (
    IncidentAlertAttachRequest,
    IncidentAlertDetachResponse,
    IncidentCreate,
    IncidentPaginationResponse,
    IncidentRead,
    IncidentResolveRequest,
    IncidentStatisticsResponse,
    IncidentUpdate,
)
from app.services.incident_command_service import (
    IncidentCommandService,
)
from app.services.incident_exceptions import (
    IncidentAlertConflictError,
    IncidentAlertNotAttachedError,
    IncidentAlertNotFoundError,
    IncidentError,
    IncidentNotFoundError,
    IncidentOwnerNotFoundError,
    IncidentResolutionError,
    InvalidIncidentTransitionError,
)
from app.services.incident_response_service import (
    IncidentResponseService,
)
from app.services.incident_service import (
    IncidentService,
)


router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"],
)


read_access = require_roles(
    UserRole.ADMIN,
    UserRole.OPERATOR,
    UserRole.VIEWER,
)

write_access = require_roles(
    UserRole.ADMIN,
    UserRole.OPERATOR,
)


def translate_incident_error(
    exc: IncidentError,
) -> HTTPException:
    """Translate domain failures into HTTP responses."""

    if isinstance(
        exc,
        (
            IncidentNotFoundError,
            IncidentAlertNotFoundError,
            IncidentOwnerNotFoundError,
        ),
    ):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if isinstance(
        exc,
        IncidentAlertNotAttachedError,
    ):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if isinstance(
        exc,
        (
            IncidentAlertConflictError,
            InvalidIncidentTransitionError,
            IncidentResolutionError,
        ),
    ):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    return HTTPException(
        status_code=(
            status.HTTP_400_BAD_REQUEST
        ),
        detail=str(exc),
    )


@router.post(
    "",
    response_model=IncidentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an operational incident",
)
def create_incident(
    incident_data: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        write_access
    ),
) -> IncidentRead:
    """Create an incident and optionally attach alert evidence."""

    del current_user

    try:
        incident = (
            IncidentCommandService.create(
                db=db,
                incident_data=incident_data,
            )
        )
    except IncidentError as exc:
        raise translate_incident_error(
            exc
        ) from exc

    return IncidentResponseService.to_read(
        incident
    )


@router.get(
    "",
    response_model=IncidentPaginationResponse,
    summary="List operational incidents",
)
def list_incidents(
    incident_status: IncidentStatus | None = Query(
        default=None,
        alias="status",
    ),
    severity: IncidentSeverity | None = Query(
        default=None,
    ),
    priority: IncidentPriority | None = Query(
        default=None,
    ),
    source: IncidentSource | None = Query(
        default=None,
    ),
    owner_id: int | None = Query(
        default=None,
        ge=1,
    ),
    active_only: bool = Query(
        default=False,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        read_access
    ),
) -> IncidentPaginationResponse:
    """Return filtered and paginated incidents."""

    del current_user

    try:
        result = IncidentService.list_incidents(
            db=db,
            status=incident_status,
            severity=severity,
            priority=priority,
            source=source,
            owner_id=owner_id,
            active_only=active_only,
            page=page,
            page_size=page_size,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail=str(exc),
        ) from exc

    return (
        IncidentResponseService.to_paginated(
            result
        )
    )


@router.get(
    "/{public_id}",
    response_model=IncidentRead,
    summary="Retrieve an incident",
)
def get_incident(
    public_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        read_access
    ),
) -> IncidentRead:
    """Return a complete incident by public ID."""

    del current_user

    try:
        incident = (
            IncidentService
            .get_required_by_public_id(
                db=db,
                public_id=public_id,
            )
        )
    except IncidentError as exc:
        raise translate_incident_error(
            exc
        ) from exc

    return IncidentResponseService.to_read(
        incident
    )


@router.patch(
    "/{public_id}",
    response_model=IncidentRead,
    summary="Update incident information",
)
def update_incident(
    public_id: str,
    incident_data: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        write_access
    ),
) -> IncidentRead:
    """Update editable incident information."""

    del current_user

    try:
        incident = (
            IncidentCommandService.update(
                db=db,
                public_id=public_id,
                incident_data=incident_data,
            )
        )
    except IncidentError as exc:
        raise translate_incident_error(
            exc
        ) from exc

    return IncidentResponseService.to_read(
        incident
    )


@router.post(
    "/{public_id}/acknowledge",
    response_model=IncidentRead,
    summary="Acknowledge an incident",
)
def acknowledge_incident(
    public_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        write_access
    ),
) -> IncidentRead:
    """Acknowledge an open incident."""

    del current_user

    try:
        incident = (
            IncidentCommandService
            .acknowledge(
                db=db,
                public_id=public_id,
            )
        )
    except IncidentError as exc:
        raise translate_incident_error(
            exc
        ) from exc

    return IncidentResponseService.to_read(
        incident
    )


@router.post(
    "/{public_id}/investigate",
    response_model=IncidentRead,
    summary="Start incident investigation",
)
def investigate_incident(
    public_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        write_access
    ),
) -> IncidentRead:
    """Move an incident into investigation."""

    del current_user

    try:
        incident = (
            IncidentCommandService
            .investigate(
                db=db,
                public_id=public_id,
            )
        )
    except IncidentError as exc:
        raise translate_incident_error(
            exc
        ) from exc

    return IncidentResponseService.to_read(
        incident
    )


@router.post(
    "/{public_id}/monitor",
    response_model=IncidentRead,
    summary="Start incident monitoring",
)
def monitor_incident(
    public_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        write_access
    ),
) -> IncidentRead:
    """Move an investigated incident into monitoring."""

    del current_user

    try:
        incident = (
            IncidentCommandService.monitor(
                db=db,
                public_id=public_id,
            )
        )
    except IncidentError as exc:
        raise translate_incident_error(
            exc
        ) from exc

    return IncidentResponseService.to_read(
        incident
    )


@router.post(
    "/{public_id}/resolve",
    response_model=IncidentRead,
    summary="Resolve an incident",
)
def resolve_incident(
    public_id: str,
    resolution_data: IncidentResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        write_access
    ),
) -> IncidentRead:
    """Resolve a monitored incident."""

    del current_user

    try:
        incident = (
            IncidentCommandService.resolve(
                db=db,
                public_id=public_id,
                resolution_data=resolution_data,
            )
        )
    except IncidentError as exc:
        raise translate_incident_error(
            exc
        ) from exc

    return IncidentResponseService.to_read(
        incident
    )


@router.post(
    "/{public_id}/alerts",
    response_model=IncidentRead,
    summary="Attach alert evidence",
)
def attach_incident_alerts(
    public_id: str,
    attachment_data: IncidentAlertAttachRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        write_access
    ),
) -> IncidentRead:
    """Attach one or more alerts to an incident."""

    del current_user

    try:
        incident = (
            IncidentCommandService
            .attach_alerts(
                db=db,
                public_id=public_id,
                attachment_data=attachment_data,
            )
        )
    except IncidentError as exc:
        raise translate_incident_error(
            exc
        ) from exc

    return IncidentResponseService.to_read(
        incident
    )


@router.delete(
    "/{public_id}/alerts/{alert_id}",
    response_model=IncidentAlertDetachResponse,
    summary="Detach alert evidence",
)
def detach_incident_alert(
    public_id: str,
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        write_access
    ),
) -> IncidentAlertDetachResponse:
    """Detach an alert from an incident."""

    del current_user

    try:
        IncidentCommandService.detach_alert(
            db=db,
            public_id=public_id,
            alert_id=alert_id,
        )
    except IncidentError as exc:
        raise translate_incident_error(
            exc
        ) from exc

    return IncidentAlertDetachResponse(
        public_id=public_id,
        alert_id=alert_id,
        detached=True,
    )


@router.get(
    "/{public_id}/statistics",
    response_model=IncidentStatisticsResponse,
    summary="Retrieve incident statistics",
)
def get_incident_statistics(
    public_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        read_access
    ),
) -> IncidentStatisticsResponse:
    """Return calculated operational incident statistics."""

    del current_user

    try:
        incident = (
            IncidentService
            .get_required_by_public_id(
                db=db,
                public_id=public_id,
            )
        )

        statistics = (
            IncidentService.get_statistics(
                db=db,
                incident=incident,
            )
        )
    except IncidentError as exc:
        raise translate_incident_error(
            exc
        ) from exc

    return (
        IncidentResponseService
        .to_statistics(statistics)
    )