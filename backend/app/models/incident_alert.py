"""Association model linking operational incidents and alerts."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import Base


if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.incident import Incident


class IncidentAlert(Base):
    """Association between an incident and one supporting alert."""

    __tablename__ = "incident_alerts"

    __table_args__ = (
        UniqueConstraint(
            "alert_id",
            name="uq_incident_alerts_alert_id",
        ),
        Index(
            "ix_incident_alerts_incident_id",
            "incident_id",
        ),
        Index(
            "ix_incident_alerts_attached_at",
            "attached_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    incident_id: Mapped[int] = mapped_column(
        ForeignKey(
            "incidents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    alert_id: Mapped[int] = mapped_column(
        ForeignKey(
            "alerts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    attached_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    incident: Mapped[Incident] = relationship(
        "Incident",
        back_populates="alert_links",
    )

    alert: Mapped[Alert] = relationship(
        "Alert",
        lazy="joined",
    )