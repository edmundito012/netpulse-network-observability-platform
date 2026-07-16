"""Incident persistence model and incident domain enums."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
    text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import Base


if TYPE_CHECKING:
    from app.models.incident_alert import IncidentAlert
    from app.models.user import User


class IncidentStatus(str, Enum):
    """Lifecycle states supported by the Incident Engine."""

    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    INVESTIGATING = "INVESTIGATING"
    MONITORING = "MONITORING"
    RESOLVED = "RESOLVED"


class IncidentSeverity(str, Enum):
    """Observed technical severity of an incident."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class IncidentPriority(str, Enum):
    """Operational priority assigned to an incident."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentSource(str, Enum):
    """Component responsible for creating an incident."""

    MANUAL = "MANUAL"
    API = "API"
    ALERT_ENGINE = "ALERT_ENGINE"
    CORRELATION_ENGINE = "CORRELATION_ENGINE"
    ROOT_CAUSE_ENGINE = "ROOT_CAUSE_ENGINE"


class Incident(Base):
    """Operational incident grouping related observability signals."""

    __tablename__ = "incidents"

    __table_args__ = (
        Index(
            "ix_incidents_status",
            "status",
        ),
        Index(
            "ix_incidents_severity",
            "severity",
        ),
        Index(
            "ix_incidents_priority",
            "priority",
        ),
        Index(
            "ix_incidents_owner_id_status",
            "owner_id",
            "status",
        ),
        Index(
            "ix_incidents_detected_at",
            "detected_at",
        ),
        Index(
            "ix_incidents_status_detected_at",
            "status",
            "detected_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    public_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        server_default=text(
            "'INC-' || "
            "to_char(CURRENT_DATE, 'YYYY') || "
            "'-' || "
            "lpad("
            "nextval('incident_public_id_seq')::text, "
            "6, "
            "'0'"
            ")"
        ),
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[IncidentStatus] = mapped_column(
        SQLEnum(
            IncidentStatus,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=IncidentStatus.OPEN,
        server_default=IncidentStatus.OPEN.value,
    )

    severity: Mapped[IncidentSeverity] = mapped_column(
        SQLEnum(
            IncidentSeverity,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=IncidentSeverity.WARNING,
        server_default=IncidentSeverity.WARNING.value,
    )

    priority: Mapped[IncidentPriority] = mapped_column(
        SQLEnum(
            IncidentPriority,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=IncidentPriority.MEDIUM,
        server_default=IncidentPriority.MEDIUM.value,
    )

    source: Mapped[IncidentSource] = mapped_column(
        SQLEnum(
            IncidentSource,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=IncidentSource.MANUAL,
        server_default=IncidentSource.MANUAL.value,
    )

    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    business_impact: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    root_cause: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    resolution_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    tags: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default=text("'[]'::json"),
    )

    incident_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
        server_default=text("'{}'::json"),
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()"),
    )

    owner: Mapped[User | None] = relationship(
        "User",
        lazy="joined",
    )

    alert_links: Mapped[list[IncidentAlert]] = relationship(
        "IncidentAlert",
        back_populates="incident",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )