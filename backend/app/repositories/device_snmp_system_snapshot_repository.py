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