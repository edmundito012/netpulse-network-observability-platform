from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.dashboard_cache import get_dashboard_state
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.dashboard import DashboardOverviewRead
from app.services.dashboard_service import DashboardService


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/overview", response_model=DashboardOverviewRead)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.OPERATOR,
            UserRole.VIEWER,
        )
    ),
):
    cached_state = get_dashboard_state()

    if cached_state:
        return cached_state

    return DashboardService.refresh_dashboard_cache(db=db)