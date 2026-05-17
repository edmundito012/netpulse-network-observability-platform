from fastapi import APIRouter, Depends

from app.api.deps import require_roles
from app.core.device_state_cache import (
    get_all_device_states,
)
from app.models.user import User, UserRole


router = APIRouter(
    prefix="/device-state",
    tags=["Device State"],
)


@router.get("/")
def get_device_states(
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.OPERATOR,
            UserRole.VIEWER,
        )
    ),
):
    return get_all_device_states()