from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.alert import AlertSeverity, AlertStatus
from app.models.device_event import DeviceEventType
from app.models.user import UserRole
from app.repositories.alert_repository import AlertRepository
from app.repositories.device_event_repository import DeviceEventRepository
from app.schemas.alert import AlertRead
from app.schemas.pagination import PaginatedResponse


router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
)


@router.get("/", response_model=PaginatedResponse[AlertRead])
def get_alerts(
    device_id: int | None = Query(default=None),
    severity: AlertSeverity | None = Query(default=None),
    status: AlertStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.OPERATOR,
            UserRole.VIEWER,
        )
    ),
):
    return AlertRepository.get_paginated(
        db=db,
        device_id=device_id,
        severity=severity,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.get("/open", response_model=list[AlertRead])
def get_open_alerts(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.OPERATOR,
            UserRole.VIEWER,
        )
    ),
):
    return AlertRepository.get_open_alerts(db)


@router.get("/{alert_id}", response_model=AlertRead)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.OPERATOR,
            UserRole.VIEWER,
        )
    ),
):
    alert = AlertRepository.get_by_id(db, alert_id)

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    return alert


@router.post("/{alert_id}/resolve", response_model=AlertRead)
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.OPERATOR,
        )
    ),
):
    alert = AlertRepository.get_by_id(db, alert_id)

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    if alert.status == AlertStatus.RESOLVED:
        return alert

    resolved_alert = AlertRepository.resolve(db, alert)

    DeviceEventRepository.create(
        db=db,
        device_id=alert.device_id,
        event_type=DeviceEventType.ALERT_RESOLVED,
        message=f"Alert resolved manually: {alert.message}",
    )

    return resolved_alert


@router.post("/{alert_id}/acknowledge", response_model=AlertRead)
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.OPERATOR,
        )
    ),
):
    alert = AlertRepository.get_by_id(db, alert_id)

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    if alert.status == AlertStatus.ACKNOWLEDGED:
        return alert

    acknowledged_alert = AlertRepository.acknowledge(db, alert)

    DeviceEventRepository.create(
        db=db,
        device_id=alert.device_id,
        event_type=DeviceEventType.ALERT_ACKNOWLEDGED,
        message=f"Alert acknowledged: {alert.message}",
    )

    return acknowledged_alert