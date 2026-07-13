"""Alert persistence model and alert domain enums."""

from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.sql import func

from app.models.base import Base


class AlertSeverity(str, Enum):
    """Operational severity assigned to an alert."""

    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class AlertStatus(str, Enum):
    """Lifecycle status of an alert."""

    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class AlertType(str, Enum):
    """Stable functional identity of an alert."""

    GENERIC = "GENERIC"
    PACKET_LOSS = "PACKET_LOSS"
    PACKET_LOSS_BURST = "PACKET_LOSS_BURST"
    JITTER = "JITTER"
    LATENCY_TREND = "LATENCY_TREND"
    FLAPPING = "FLAPPING"
    PREDICTIVE = "PREDICTIVE"


def generate_legacy_deduplication_key() -> str:
    """Generate a unique identity for directly constructed legacy alerts.

    Alert-producing application services provide deterministic keys such
    as ``device:10:packet_loss``. Direct ORM construction, retained for
    backwards compatibility and tests, receives an isolated legacy key
    so unrelated generic alerts are never incorrectly deduplicated.
    """

    return f"legacy:{uuid4().hex}"


class Alert(Base):
    """Operational alert generated for a monitored device."""

    __tablename__ = "alerts"

    __table_args__ = (
        Index(
            "ix_alerts_status",
            "status",
        ),
        Index(
            "ix_alerts_device_id_status",
            "device_id",
            "status",
        ),
        Index(
            "ix_alerts_device_id_deduplication_key",
            "device_id",
            "deduplication_key",
        ),
        Index(
            "ix_alerts_alert_type",
            "alert_type",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    device_id = Column(
        Integer,
        ForeignKey(
            "devices.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    alert_type = Column(
        SQLEnum(
            AlertType,
            native_enum=False,
            length=50,
        ),
        nullable=False,
        default=AlertType.GENERIC,
    )

    deduplication_key = Column(
        String(255),
        nullable=False,
        default=generate_legacy_deduplication_key,
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

    message = Column(
        String,
        nullable=False,
    )

    occurrence_count = Column(
        Integer,
        nullable=False,
        default=1,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    first_seen_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    last_seen_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    resolved_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )