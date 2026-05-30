from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class DeviceEventType(str, Enum):
    DEVICE_ONLINE = "DEVICE_ONLINE"
    DEVICE_OFFLINE = "DEVICE_OFFLINE"

    ALERT_CREATED = "ALERT_CREATED"
    ALERT_ACKNOWLEDGED = "ALERT_ACKNOWLEDGED"
    ALERT_RESOLVED = "ALERT_RESOLVED"

    SNMP_SNAPSHOT_COLLECTED = "SNMP_SNAPSHOT_COLLECTED"


class DeviceEvent(Base):
    __tablename__ = "device_events"

    __table_args__ = (
        Index("ix_device_events_device_id_created_at", "device_id", "created_at"),
        Index("ix_device_events_event_type", "event_type"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id"),
        nullable=False,
    )

    event_type: Mapped[DeviceEventType] = mapped_column(
        SqlEnum(DeviceEventType),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )