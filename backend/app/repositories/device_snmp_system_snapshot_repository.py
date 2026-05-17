from sqlalchemy.orm import Session

from app.models.device_snmp_system_snapshot import (
    DeviceSNMPSystemSnapshot,
)


class DeviceSNMPSystemSnapshotRepository:

    @staticmethod
    def create(
        db: Session,
        device_id: int,
        sysdescr: str,
        sysuptime: str,
        syscontact: str,
        sysname: str,
        syslocation: str,
    ):
        snapshot = DeviceSNMPSystemSnapshot(
            device_id=device_id,
            sysdescr=sysdescr,
            sysuptime=sysuptime,
            syscontact=syscontact,
            sysname=sysname,
            syslocation=syslocation,
        )

        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

        return snapshot

    @staticmethod
    def get_by_device_id(
        db: Session,
        device_id: int,
        limit: int = 50,
    ):
        return (
            db.query(DeviceSNMPSystemSnapshot)
            .filter(DeviceSNMPSystemSnapshot.device_id == device_id)
            .order_by(DeviceSNMPSystemSnapshot.collected_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_latest_by_device(
        db: Session,
        device_id: int,
    ):
        return (
            db.query(DeviceSNMPSystemSnapshot)
            .filter(DeviceSNMPSystemSnapshot.device_id == device_id)
            .order_by(DeviceSNMPSystemSnapshot.collected_at.desc())
            .first()
        )

    @staticmethod
    def get_paginated_by_device_id(
        db: Session,
        device_id: int,
        page: int = 1,
        page_size: int = 20,
    ):
        query = db.query(DeviceSNMPSystemSnapshot).filter(
            DeviceSNMPSystemSnapshot.device_id == device_id
        )

        total_count = query.count()

        items = (
            query
            .order_by(DeviceSNMPSystemSnapshot.collected_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        total_pages = (
            (total_count + page_size - 1) // page_size
            if total_count > 0
            else 0
        )

        return {
            "items": items,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }