from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.device import DeviceCreate, DeviceRead, DeviceUpdate
from app.services.device_service import DeviceService


router = APIRouter(
    prefix="/devices",
    tags=["Devices"]
)


@router.get("/", response_model=list[DeviceRead])
def list_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER)
    )
):
    return DeviceService.get_devices(db)


@router.post("/", response_model=DeviceRead)
def create_device(
    device_data: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.OPERATOR)
    )
):
    try:
        return DeviceService.create_device(
            db=db,
            device_data=device_data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get("/{device_id}", response_model=DeviceRead)
def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER)
    )
):
    try:
        return DeviceService.get_device(
            db=db,
            device_id=device_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


@router.put("/{device_id}", response_model=DeviceRead)
def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.OPERATOR)
    )
):
    try:
        return DeviceService.update_device(
            db=db,
            device_id=device_id,
            device_data=device_data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


@router.delete("/{device_id}")
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN)
    )
):
    try:
        DeviceService.delete_device(
            db=db,
            device_id=device_id
        )

        return {"message": "Device deleted successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )