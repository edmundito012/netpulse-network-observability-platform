"""add incident correlations

Revision ID: e9b7c4a12d63
Revises: d8f31a72c640
Create Date: 2026-07-18 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e9b7c4a12d63"

down_revision: str | Sequence[str] | None = (
    "d8f31a72c640"
)

branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create explainable alert correlation persistence."""

    op.create_table(
        "incident_correlations",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "correlation_key",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "source_alert_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "target_incident_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "outcome",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "application_status",
            sa.String(length=32),
            server_default="EVALUATED",
            nullable=False,
        ),
        sa.Column(
            "signal_family",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "score",
            sa.Numeric(
                precision=5,
                scale=4,
            ),
            nullable=False,
        ),
        sa.Column(
            "threshold",
            sa.Numeric(
                precision=5,
                scale=4,
            ),
            nullable=False,
        ),
        sa.Column(
            "reasons",
            sa.JSON(),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
        sa.Column(
            "candidate_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "window_seconds",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "explanation",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "metadata",
            sa.JSON(),
            server_default=sa.text("'{}'::json"),
            nullable=False,
        ),
        sa.Column(
            "failure_reason",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "evaluated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "applied_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.CheckConstraint(
            "outcome IN ("
            "'MATCHED_EXISTING', "
            "'CREATE_NEW', "
            "'NO_ACTION'"
            ")",
            name=(
                "ck_incident_correlations_"
                "outcome"
            ),
        ),
        sa.CheckConstraint(
            "application_status IN ("
            "'EVALUATED', "
            "'APPLIED', "
            "'FAILED'"
            ")",
            name=(
                "ck_incident_correlations_"
                "application_status"
            ),
        ),
        sa.CheckConstraint(
            "signal_family IN ("
            "'CONNECTIVITY', "
            "'PERFORMANCE', "
            "'STABILITY', "
            "'EXPERIENCE', "
            "'PREDICTIVE', "
            "'GENERIC'"
            ")",
            name=(
                "ck_incident_correlations_"
                "signal_family"
            ),
        ),
        sa.CheckConstraint(
            "score >= 0 AND score <= 1",
            name=(
                "ck_incident_correlations_"
                "score_range"
            ),
        ),
        sa.CheckConstraint(
            "threshold >= 0 AND threshold <= 1",
            name=(
                "ck_incident_correlations_"
                "threshold_range"
            ),
        ),
        sa.CheckConstraint(
            "candidate_count >= 0",
            name=(
                "ck_incident_correlations_"
                "candidate_count_non_negative"
            ),
        ),
        sa.CheckConstraint(
            "window_seconds >= 60",
            name=(
                "ck_incident_correlations_"
                "window_seconds_minimum"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["source_alert_id"],
            ["alerts.id"],
            name=(
                "fk_incident_correlations_"
                "source_alert_id_alerts"
            ),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_incident_id"],
            ["incidents.id"],
            name=(
                "fk_incident_correlations_"
                "target_incident_id_incidents"
            ),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_incident_correlations",
        ),
        sa.UniqueConstraint(
            "correlation_key",
            name=(
                "uq_incident_correlations_"
                "correlation_key"
            ),
        ),
    )

    op.create_index(
        (
            "ix_incident_correlations_"
            "correlation_key"
        ),
        "incident_correlations",
        ["correlation_key"],
        unique=True,
    )

    op.create_index(
        (
            "ix_incident_correlations_"
            "source_alert"
        ),
        "incident_correlations",
        ["source_alert_id"],
        unique=False,
    )

    op.create_index(
        (
            "ix_incident_correlations_"
            "target_incident_evaluated"
        ),
        "incident_correlations",
        [
            "target_incident_id",
            "evaluated_at",
        ],
        unique=False,
    )

    op.create_index(
        (
            "ix_incident_correlations_"
            "outcome_status"
        ),
        "incident_correlations",
        [
            "outcome",
            "application_status",
        ],
        unique=False,
    )

    op.create_index(
        (
            "ix_incident_correlations_"
            "signal_family"
        ),
        "incident_correlations",
        ["signal_family"],
        unique=False,
    )

    op.create_index(
        (
            "ix_incident_correlations_"
            "evaluated_at"
        ),
        "incident_correlations",
        ["evaluated_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove correlation persistence."""

    op.drop_index(
        (
            "ix_incident_correlations_"
            "evaluated_at"
        ),
        table_name="incident_correlations",
    )

    op.drop_index(
        (
            "ix_incident_correlations_"
            "signal_family"
        ),
        table_name="incident_correlations",
    )

    op.drop_index(
        (
            "ix_incident_correlations_"
            "outcome_status"
        ),
        table_name="incident_correlations",
    )

    op.drop_index(
        (
            "ix_incident_correlations_"
            "target_incident_evaluated"
        ),
        table_name="incident_correlations",
    )

    op.drop_index(
        (
            "ix_incident_correlations_"
            "source_alert"
        ),
        table_name="incident_correlations",
    )

    op.drop_index(
        (
            "ix_incident_correlations_"
            "correlation_key"
        ),
        table_name="incident_correlations",
    )

    op.drop_table(
        "incident_correlations"
    )