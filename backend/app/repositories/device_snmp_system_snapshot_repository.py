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