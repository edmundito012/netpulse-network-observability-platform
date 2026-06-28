from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.notification_log import (
    NotificationLogRead,
)

from app.services.notification_log_service import (
    NotificationLogService,
)

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get(
    "/history",
    response_model=list[
        NotificationLogRead
    ],
)
def get_notification_history(
    db: Session = Depends(get_db),
):
    return (
        NotificationLogService
        .get_history(db)
    )