"""Correlation Engine HTTP API."""

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.correlation import (
    CorrelationApplicationStatus,
    CorrelationConfiguration,
    CorrelationOutcome,
    CorrelationSignalFamily,
)
from app.db.session import get_db
from app.models.user import (
    User,
    UserRole,
)
from app.schemas.incident_correlation import (
    IncidentCorrelationPaginationResponse,
    IncidentCorrelationRead,
)
from app.schemas.incident_correlation_api import (
    CorrelationEvaluationResponse,
    CorrelationExecutionOptions,
)
from app.schemas.incident_correlation_application import (
    CorrelationApplicationResult,
)
from app.services.incident_correlation_application_service import (
    CorrelationApplicationError,
    IncidentCorrelationApplicationService,
)
from app.services.incident_correlation_query_service import (
    IncidentCorrelationNotFoundError,
    IncidentCorrelationQueryService,
)
from app.services.incident_correlation_service import (
    IncidentCorrelationService,
    SourceAlertNotFoundError,
)
from app.services.incident_exceptions import (
    IncidentAlertConflictError,
    IncidentError,
)


router = APIRouter(
    prefix="/incident-correlations",
    tags=["Incident Correlations"],
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


def build_configuration(
    options: CorrelationExecutionOptions,
) -> CorrelationConfiguration:
    """Convert validated HTTP options into domain configuration."""

    return CorrelationConfiguration(
        window_seconds=options.window_seconds,
        threshold=options.threshold,
        max_candidates=options.max_candidates,
    )


def translate_correlation_error(
    exc: Exception,
) -> HTTPException:
    """Translate correlation-domain failures into HTTP responses."""

    if isinstance(
        exc,
        (
            SourceAlertNotFoundError,
            IncidentCorrelationNotFoundError,
        ),
    ):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if isinstance(
        exc,
        IncidentAlertConflictError,
    ):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if isinstance(
        exc,
        (
            CorrelationApplicationError,
            IncidentError,
        ),
    ):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if isinstance(
        exc,
        ValueError,
    ):
        return HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail=str(exc),
        )

    return HTTPException(
        status_code=(
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ),
        detail=(
            "Correlation Engine operation failed"
        ),
    )


@router.post(
    "/evaluate/{alert_id}",
    response_model=CorrelationEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate an alert for incident correlation",
)
def evaluate_alert_correlation(
    alert_id: int,
    options: CorrelationExecutionOptions = Body(
        default={},
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        write_access
    ),
) -> CorrelationEvaluationResponse:
    """Evaluate and persist a decision without applying it."""

    del current_user

    try:
        (
            evaluation,
            correlation,
            persistence_created,
        ) = (
            IncidentCorrelationService
            .evaluate_and_persist(
                db=db,
                source_alert_id=alert_id,
                configuration=(
                    build_configuration(
                        options
                    )
                ),
            )
        )

    except Exception as exc:
        raise translate_correlation_error(
            exc
        ) from exc

    return CorrelationEvaluationResponse(
        **evaluation.model_dump(),
        correlation_id=correlation.id,
        persistence_created=(
            persistence_created
        ),
    )


@router.post(
    "/apply/{alert_id}",
    response_model=CorrelationApplicationResult,
    status_code=status.HTTP_200_OK,
    summary="Evaluate and apply an alert correlation",
)
def apply_alert_correlation(
    alert_id: int,
    options: CorrelationExecutionOptions = Body(
        default={},
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        write_access
    ),
) -> CorrelationApplicationResult:
    """Evaluate, persist and apply a correlation decision."""

    del current_user

    try:
        return (
            IncidentCorrelationApplicationService
            .evaluate_and_apply(
                db=db,
                source_alert_id=alert_id,
                configuration=(
                    build_configuration(
                        options
                    )
                ),
            )
        )

    except Exception as exc:
        raise translate_correlation_error(
            exc
        ) from exc


@router.get(
    "",
    response_model=(
        IncidentCorrelationPaginationResponse
    ),
    summary="List persisted correlation decisions",
)
def list_incident_correlations(
    source_alert_id: int | None = Query(
        default=None,
        ge=1,
    ),
    target_incident_id: int | None = Query(
        default=None,
        ge=1,
    ),
    outcome: CorrelationOutcome | None = Query(
        default=None,
    ),
    application_status: (
        CorrelationApplicationStatus | None
    ) = Query(
        default=None,
    ),
    signal_family: (
        CorrelationSignalFamily | None
    ) = Query(
        default=None,
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
) -> IncidentCorrelationPaginationResponse:
    """Return filtered correlation history."""

    del current_user

    try:
        result = (
            IncidentCorrelationQueryService
            .list_correlations(
                db=db,
                source_alert_id=source_alert_id,
                target_incident_id=(
                    target_incident_id
                ),
                outcome=outcome,
                application_status=(
                    application_status
                ),
                signal_family=signal_family,
                page=page,
                page_size=page_size,
            )
        )

    except Exception as exc:
        raise translate_correlation_error(
            exc
        ) from exc

    return (
        IncidentCorrelationPaginationResponse
        .model_validate(
            result
        )
    )


@router.get(
    "/{correlation_id}",
    response_model=IncidentCorrelationRead,
    summary="Retrieve a persisted correlation decision",
)
def get_incident_correlation(
    correlation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        read_access
    ),
) -> IncidentCorrelationRead:
    """Return one persisted correlation decision."""

    del current_user

    try:
        correlation = (
            IncidentCorrelationQueryService
            .get_required(
                db=db,
                correlation_id=correlation_id,
            )
        )

    except Exception as exc:
        raise translate_correlation_error(
            exc
        ) from exc

    return IncidentCorrelationRead.model_validate(
        correlation
    )