from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.sql import func

from app.models.base import Base


class AlertSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class AlertStatus(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class Alert(Base):
    __tablename__ = "alerts"

    __table_args__ = (
        Index("ix_alerts_status", "status"),
        Index("ix_alerts_device_id_status", "device_id", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)

    device_id = Column(
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    severity = Column(
        SQLEnum(AlertSeverity),
        nullable=False,
    )

    status = Column(
        SQLEnum(AlertStatus),
        nullable=False,
        default=AlertStatus.OPEN,
    )

    message = Column(String, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    resolved_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )