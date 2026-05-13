from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.device import DeviceStatus


class DeviceMetric(Base):
    __tablename__ = "device_metrics"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id"),
        nullable=False,
        index=True
    )

    status: Mapped[DeviceStatus] = mapped_column(
        Enum(DeviceStatus),
        nullable=False
    )

    response_time_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    checked_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )