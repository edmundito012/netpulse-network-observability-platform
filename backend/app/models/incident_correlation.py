"""Persistence model for explainable incident correlations."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.core.correlation import (
    CorrelationApplicationStatus,
    CorrelationOutcome,
    CorrelationSignalFamily,
)
from app.models.base import Base


if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.incident import Incident


class IncidentCorrelation(Base):
    """Explainable decision linking an alert to an incident."""

    __tablename__ = "incident_correlations"

    __table_args__ = (
        CheckConstraint(
            "score >= 0 AND score <= 1",
            name=(
                "ck_incident_correlations_"
                "score_range"
            ),
        ),
        CheckConstraint(
            "threshold >= 0 AND threshold <= 1",
            name=(
                "ck_incident_correlations_"
                "threshold_range"
            ),
        ),
        CheckConstraint(
            "candidate_count >= 0",
            name=(
                "ck_incident_correlations_"
                "candidate_count_non_negative"
            ),
        ),
        CheckConstraint(
            "window_seconds >= 60",
            name=(
                "ck_incident_correlations_"
                "window_seconds_minimum"
            ),
        ),
        Index(
            "ix_incident_correlations_source_alert",
            "source_alert_id",
        ),
        Index(
            (
                "ix_incident_correlations_"
                "target_incident_evaluated"
            ),
            "target_incident_id",
            "evaluated_at",
        ),
        Index(
            (
                "ix_incident_correlations_"
                "outcome_status"
            ),
            "outcome",
            "application_status",
        ),
        Index(
            (
                "ix_incident_correlations_"
                "signal_family"
            ),
            "signal_family",
        ),
        Index(
            (
                "ix_incident_correlations_"
                "evaluated_at"
            ),
            "evaluated_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    correlation_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    source_alert_id: Mapped[int] = mapped_column(
        ForeignKey(
            "alerts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    target_incident_id: Mapped[
        int | None
    ] = mapped_column(
        ForeignKey(
            "incidents.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    outcome: Mapped[
        CorrelationOutcome
    ] = mapped_column(
        SQLEnum(
            CorrelationOutcome,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )

    application_status: Mapped[
        CorrelationApplicationStatus
    ] = mapped_column(
        SQLEnum(
            CorrelationApplicationStatus,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=(
            CorrelationApplicationStatus.EVALUATED
        ),
        server_default=(
            CorrelationApplicationStatus
            .EVALUATED
            .value
        ),
    )

    signal_family: Mapped[
        CorrelationSignalFamily
    ] = mapped_column(
        SQLEnum(
            CorrelationSignalFamily,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )

    score: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=5,
            scale=4,
        ),
        nullable=False,
    )

    threshold: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=5,
            scale=4,
        ),
        nullable=False,
    )

    reasons: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default=text("'[]'::json"),
    )

    candidate_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    window_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    correlation_metadata: Mapped[
        dict[str, Any]
    ] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
        server_default=text("'{}'::json"),
    )

    failure_reason: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    applied_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    source_alert: Mapped[Alert] = relationship(
        "Alert",
        lazy="joined",
    )

    target_incident: Mapped[
        Incident | None
    ] = relationship(
        "Incident",
        lazy="joined",
    )