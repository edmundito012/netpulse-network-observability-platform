from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm import Session
from fastapi import Depends

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.device import DeviceCreate, DeviceRead, DeviceUpdate
from app.services.device_service import DeviceService
from app.schemas.device_metric import DeviceMetricRead
from app.repositories.device_metric_repository import DeviceMetricRepository
from app.services.snmp_service import SNMPService


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

@router.post("/{device_id}/ping", response_model=DeviceRead)
def ping_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.OPERATOR)
    )
):
    try:
        return DeviceService.ping_device(
            db=db,
            device_id=device_id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

@router.get(
    "/{device_id}/metrics",
    response_model=list[DeviceMetricRead]
)
def get_device_metrics(
    device_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.OPERATOR,
            UserRole.VIEWER
        )
    )
):
    return DeviceMetricRepository.get_by_device_id(
        db=db,
        device_id=device_id,
        limit=limit
    )

@router.get("/{device_id}/snmp/sysdescr")
async def get_device_sysdescr(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.OPERATOR,
            UserRole.VIEWER
        )
    )
):
    try:
        device = DeviceService.get_device(
            db=db,
            device_id=device_id
        )

        sysdescr = await SNMPService.get_sysdescr(
            ip_address=device.ip_address
        )

        return {
            "device_id": device.id,
            "ip_address": device.ip_address,
            "sysdescr": sysdescr
        }

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