from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.logging import logger
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import UserService


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserRead,
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    try:
        user = UserService.create_user(
            db=db,
            user_data=user_data,
        )

        logger.info(
            "User registered successfully: %s",
            user.email,
        )

        return user

    except ValueError as e:
        logger.warning(
            "User registration failed for email %s: %s",
            user_data.email,
            e,
        )

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    try:
        token = UserService.authenticate_user(
            db=db,
            email=form_data.username,
            password=form_data.password,
        )

        logger.info(
            "User login successful: %s",
            form_data.username,
        )

        return TokenResponse(
            access_token=token,
        )

    except ValueError as e:
        logger.warning(
            "User login failed for email %s: %s",
            form_data.username,
            e,
        )

        raise HTTPException(
            status_code=401,
            detail=str(e),
        )


@router.get(
    "/me",
    response_model=UserRead,
)
def read_current_user(
    current_user: User = Depends(get_current_user),
):
    logger.info(
        "Current user profile requested: %s",
        current_user.email,
    )

    return current_user


@router.get("/admin-only")
def admin_only(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info(
        "Admin-only endpoint accessed by: %s",
        current_user.email,
    )

    return {
        "message": "Admin access granted",
        "user": current_user.email,
    }


@router.get("/operator-only")
def operator_only(
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.OPERATOR,
        )
    ),
):
    logger.info(
        "Operator endpoint accessed by: %s with role %s",
        current_user.email,
        current_user.role,
    )

    return {
        "message": "Operator access granted",
        "user": current_user.email,
        "role": current_user.role,
    }


@router.get("/viewer-or-above")
def viewer_or_above(
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.OPERATOR,
            UserRole.VIEWER,
        )
    ),
):
    logger.info(
        "Viewer endpoint accessed by: %s with role %s",
        current_user.email,
        current_user.role,
    )

    return {
        "message": "Viewer access granted",
        "user": current_user.email,
        "role": current_user.role,
    }