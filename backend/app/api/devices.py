from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from fastapi import Query
from app.repositories.device_event_repository import DeviceEventRepository
from app.schemas.device_event import DeviceEventRead

from app.api.deps import require_roles
from app.db.session import get_db

from app.models.user import User, UserRole

from app.schemas.device import (
    DeviceCreate,
    DeviceRead,
    DeviceUpdate,
)

from app.schemas.device_metric import DeviceMetricRead

from app.services.device_service import DeviceService
from app.services.snmp_service import SNMPService

from app.repositories.device_metric_repository import (
    DeviceMetricRepository,
)
from app.repositories.device_repository import (
    DeviceRepository,
)
from app.repositories.device_repository import DeviceRepository
from app.repositories.device_metric_repository import DeviceMetricRepository
from app.repositories.device_snmp_system_snapshot_repository import (
    DeviceSNMPSystemSnapshotRepository,
)

from app.schemas.device_summary import DeviceSummaryRead
from app.services.device_summary_service import DeviceSummaryService

from app.schemas.device_event import DeviceEventRead
from app.schemas.pagination import PaginatedResponse

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

@router.get("/{device_id}/snmp/system")
async def get_device_snmp_system(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.OPERATOR,
            UserRole.VIEWER,
        )
    ),
):
    device = DeviceRepository.get_by_id(db, device_id)

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    try:
        system_info = await SNMPService.get_system_info(
            ip_address=device.ip_address,
        )

        return {
            "device_id": device.id,
            "ip_address": device.ip_address,
            **system_info,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"SNMP error: {str(e)}",
        )

@router.get("/{device_id}/snmp/system/snapshots")
def get_device_snmp_system_snapshots(
    device_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.OPERATOR,
            UserRole.VIEWER,
        )
    ),
):
    device = DeviceRepository.get_by_id(db, device_id)

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    return DeviceSNMPSystemSnapshotRepository.get_by_device_id(
        db=db,
        device_id=device.id,
        limit=limit,
    )

@router.post("/{device_id}/snmp/system/snapshot")
async def create_device_snmp_system_snapshot(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.OPERATOR,
        )
    ),
):
    device = DeviceRepository.get_by_id(db, device_id)

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    try:
        system_info = await SNMPService.get_system_info(
            ip_address=device.ip_address,
        )

        snapshot = DeviceSNMPSystemSnapshotRepository.create(
            db=db,
            device_id=device.id,
            sysdescr=system_info.get("sysdescr"),
            sysuptime=system_info.get("sysuptime"),
            syscontact=system_info.get("syscontact"),
            sysname=system_info.get("sysname"),
            syslocation=system_info.get("syslocation"),
        )

        return snapshot

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"SNMP error: {str(e)}",
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

@router.get("/{device_id}/summary", response_model=DeviceSummaryRead)
def get_device_summary(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.OPERATOR,
            UserRole.VIEWER,
        )
    ),
):
    summary = DeviceSummaryService.get_summary(
        db=db,
        device_id=device_id,
    )

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    return summary


@router.get("/{device_id}/events",response_model=PaginatedResponse[DeviceEventRead],
)
def get_device_events(
    device_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.OPERATOR,
            UserRole.VIEWER,
        )
    ),
):
    return DeviceEventRepository.get_paginated(
        db=db,
        device_id=device_id,
        page=page,
        page_size=page_size,
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