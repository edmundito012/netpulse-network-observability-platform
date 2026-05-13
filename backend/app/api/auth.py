from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.user_service import UserService
from app.api.deps import get_current_user, require_roles
from app.models.user import User, UserRole
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=UserRead
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):

    try:
        user = UserService.create_user(
            db=db,
            user_data=user_data
        )

        return user

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post(
    "/login",
    response_model=TokenResponse
)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    try:
        token = UserService.authenticate_user(
            db=db,
            email=form_data.username,
            password=form_data.password
        )

        return TokenResponse(
            access_token=token
        )

    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )
@router.get(
    "/me",
    response_model=UserRead
)
def read_current_user(
    current_user: User = Depends(get_current_user)
):

    return current_user

@router.get("/admin-only")
def admin_only(
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    return {
        "message": "Admin access granted",
        "user": current_user.email
    }