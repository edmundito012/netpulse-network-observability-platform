from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.models.base import Base


class DeviceSNMPSystemSnapshot(Base):
    __tablename__ = "device_snmp_system_snapshots"

    id = Column(Integer, primary_key=True, index=True)

    device_id = Column(
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sysdescr = Column(String, nullable=True)
    sysuptime = Column(String, nullable=True)
    syscontact = Column(String, nullable=True)
    sysname = Column(String, nullable=True)
    syslocation = Column(String, nullable=True)

    collected_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )