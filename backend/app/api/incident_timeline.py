"""Incident Timeline HTTP API."""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.incident_timeline_event import (
    IncidentTimelineActorType,
    IncidentTimelineEventType,
)
from app.models.user import (
    User,
    UserRole,
)
from app.schemas.incident_timeline import (
    IncidentTimelineCommentCreate,
    IncidentTimelineEventRead,
    IncidentTimelinePaginationResponse,
    IncidentTimelineSummary,
)
from app.services.incident_exceptions import (
    IncidentError,
)
from app.services.incident_service import (
    IncidentService,
)
from app.services.incident_timeline_exceptions import (
    IncidentTimelineError,
)
from app.services.incident_timeline_service import (
    IncidentTimelineService,
)


router = APIRouter(
    prefix="/incidents/{public_id}/timeline",
    tags=["Incident Timeline"],
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


def translate_timeline_error(
    exc: Exception,
) -> HTTPException:
    """Translate timeline and incident domain errors."""

    if isinstance(exc, IncidentError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if isinstance(
        exc,
        IncidentTimelineError,
    ):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )


@router.get(
    "",
    response_model=IncidentTimelinePaginationResponse,
    summary="Retrieve an incident timeline",
)
def list_incident_timeline(
    public_id: str,
    event_type: (
        IncidentTimelineEventType | None
    ) = Query(
        default=None,
    ),
    actor_type: (
        IncidentTimelineActorType | None
    ) = Query(
        default=None,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    newest_first: bool = Query(
        default=False,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        read_access
    ),
) -> IncidentTimelinePaginationResponse:
    """Return filtered timeline events for one incident."""

    del current_user

    try:
        return IncidentTimelineService.list_events(
            db=db,
            public_id=public_id,
            event_type=event_type,
            actor_type=actor_type,
            page=page,
            page_size=page_size,
            newest_first=newest_first,
        )

    except (
        IncidentError,
        IncidentTimelineError,
    ) as exc:
        raise translate_timeline_error(
            exc
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail=str(exc),
        ) from exc


@router.get(
    "/summary",
    response_model=IncidentTimelineSummary,
    summary="Retrieve timeline statistics",
)
def get_incident_timeline_summary(
    public_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        read_access
    ),
) -> IncidentTimelineSummary:
    """Return aggregate timeline information."""

    del current_user

    try:
        return (
            IncidentTimelineService.get_summary(
                db=db,
                public_id=public_id,
            )
        )

    except (
        IncidentError,
        IncidentTimelineError,
    ) as exc:
        raise translate_timeline_error(
            exc
        ) from exc


@router.get(
    "/latest",
    response_model=(
        IncidentTimelineEventRead | None
    ),
    summary="Retrieve the latest timeline event",
)
def get_latest_incident_timeline_event(
    public_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        read_access
    ),
) -> IncidentTimelineEventRead | None:
    """Return the most recently recorded event."""

    del current_user

    try:
        event = (
            IncidentTimelineService
            .get_latest_event(
                db=db,
                public_id=public_id,
            )
        )

    except (
        IncidentError,
        IncidentTimelineError,
    ) as exc:
        raise translate_timeline_error(
            exc
        ) from exc

    if event is None:
        return None

    return (
        IncidentTimelineEventRead
        .model_validate(event)
    )


@router.post(
    "/comments",
    response_model=IncidentTimelineEventRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add an operator timeline comment",
)
def add_incident_timeline_comment(
    public_id: str,
    comment_data: IncidentTimelineCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        write_access
    ),
) -> IncidentTimelineEventRead:
    """Append an attributed operator comment."""

    try:
        incident = (
            IncidentService
            .get_required_by_public_id(
                db=db,
                public_id=public_id,
            )
        )

        event = (
            IncidentTimelineService.add_comment(
                db=db,
                incident=incident,
                comment_data=comment_data,
                actor_id=current_user.id,
                actor_label=current_user.username,
            )
        )

    except (
        IncidentError,
        IncidentTimelineError,
    ) as exc:
        raise translate_timeline_error(
            exc
        ) from exc

    return (
        IncidentTimelineEventRead
        .model_validate(event)
    )