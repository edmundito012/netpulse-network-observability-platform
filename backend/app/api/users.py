from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.audit_log_service import AuditLogService


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get("/", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    return UserRepository.get_all(db)


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    user = UserRepository.get_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    if UserRepository.get_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    if UserRepository.get_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    hashed_password = hash_password(user_data.password)

    created_user = UserRepository.create(
        db=db,
        user_data=user_data,
        hashed_password=hashed_password,
    )

    AuditLogService.log(
        db=db,
        user_id=current_user.id,
        action="CREATE_USER",
        resource_type="USER",
        resource_id=created_user.id,
        details={
            "email": created_user.email,
            "username": created_user.username,
            "role": created_user.role.value,
        },
    )

    return created_user


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    user = UserRepository.get_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user_data.email and user_data.email != user.email:
        existing_user = UserRepository.get_by_email(db, user_data.email)

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    if user_data.username and user_data.username != user.username:
        existing_user = UserRepository.get_by_username(db, user_data.username)

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

    hashed_password = None

    if user_data.password:
        hashed_password = hash_password(user_data.password)

    updated_user = UserRepository.update(
        db=db,
        user=user,
        user_data=user_data,
        hashed_password=hashed_password,
    )

    AuditLogService.log(
        db=db,
        user_id=current_user.id,
        action="UPDATE_USER",
        resource_type="USER",
        resource_id=updated_user.id,
        details={
            "email": updated_user.email,
            "username": updated_user.username,
            "role": updated_user.role.value,
            "is_active": updated_user.is_active,
        },
    )

    return updated_user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    user = UserRepository.get_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own user",
        )

    deleted_user_email = user.email
    deleted_username = user.username

    UserRepository.delete(db, user)

    AuditLogService.log(
        db=db,
        user_id=current_user.id,
        action="DELETE_USER",
        resource_type="USER",
        resource_id=user_id,
        details={
            "email": deleted_user_email,
            "username": deleted_username,
        },
    )

    return {"message": "User deleted successfully"}