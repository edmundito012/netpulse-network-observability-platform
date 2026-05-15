from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.device_event import DeviceEventType
from app.models.user import UserRole
from app.repositories.device_event_repository import DeviceEventRepository
from app.schemas.device_event import DeviceEventRead


router = APIRouter(
    prefix="/events",
    tags=["Events"],
)


@router.get("/", response_model=list[DeviceEventRead])
def get_events(
    device_id: int | None = Query(default=None),
    event_type: DeviceEventType | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.OPERATOR,
            UserRole.VIEWER,
        )
    ),
):
    return DeviceEventRepository.get_all(
        db=db,
        device_id=device_id,
        event_type=event_type,
        limit=limit,
    )