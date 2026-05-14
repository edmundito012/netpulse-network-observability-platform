from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import UserRole
from app.repositories.alert_repository import AlertRepository
from app.schemas.alert import AlertRead
from app.api.deps import require_roles


router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
)


@router.get("/", response_model=list[AlertRead])
def get_alerts(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.OPERATOR,
            UserRole.VIEWER,
        )
    ),
):
    return AlertRepository.get_all(db)


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

    if alert.status.value == "RESOLVED":
        return alert

    return AlertRepository.resolve(db, alert)