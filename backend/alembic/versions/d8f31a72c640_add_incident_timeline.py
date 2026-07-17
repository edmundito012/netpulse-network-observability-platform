"""add incident timeline

Revision ID: d8f31a72c640
Revises: c7e4a91d2f10
Create Date: 2026-07-17 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d8f31a72c640"

down_revision: str | Sequence[str] | None = (
    "c7e4a91d2f10"
)

branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create immutable incident timeline persistence."""

    op.create_table(
        "incident_timeline_events",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "incident_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "actor_type",
            sa.String(length=32),
            server_default="SYSTEM",
            nullable=False,
        ),
        sa.Column(
            "actor_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "actor_label",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "message",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "previous_value",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "new_value",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "metadata",
            sa.JSON(),
            server_default=sa.text("'{}'::json"),
            nullable=False,
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "event_type IN ("
            "'INCIDENT_CREATED', "
            "'STATUS_CHANGED', "
            "'ALERT_ATTACHED', "
            "'ALERT_DETACHED', "
            "'OWNER_ASSIGNED', "
            "'OWNER_UNASSIGNED', "
            "'SEVERITY_CHANGED', "
            "'PRIORITY_CHANGED', "
            "'DETAILS_UPDATED', "
            "'BUSINESS_IMPACT_UPDATED', "
            "'ROOT_CAUSE_UPDATED', "
            "'COMMENT_ADDED', "
            "'INCIDENT_RESOLVED', "
            "'AUTOMATION_ACTION'"
            ")",
            name=(
                "ck_incident_timeline_events_"
                "event_type"
            ),
        ),
        sa.CheckConstraint(
            "actor_type IN ("
            "'USER', "
            "'SYSTEM', "
            "'API', "
            "'AUTOMATION'"
            ")",
            name=(
                "ck_incident_timeline_events_"
                "actor_type"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["incidents.id"],
            name=(
                "fk_incident_timeline_events_"
                "incident_id_incidents"
            ),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name=(
                "fk_incident_timeline_events_"
                "actor_id_users"
            ),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_incident_timeline_events",
        ),
    )

    op.create_index(
        (
            "ix_incident_timeline_events_"
            "incident_occurred"
        ),
        "incident_timeline_events",
        [
            "incident_id",
            "occurred_at",
        ],
        unique=False,
    )

    op.create_index(
        (
            "ix_incident_timeline_events_"
            "event_type"
        ),
        "incident_timeline_events",
        ["event_type"],
        unique=False,
    )

    op.create_index(
        (
            "ix_incident_timeline_events_"
            "actor_id"
        ),
        "incident_timeline_events",
        ["actor_id"],
        unique=False,
    )

    op.create_index(
        (
            "ix_incident_timeline_events_"
            "occurred_at"
        ),
        "incident_timeline_events",
        ["occurred_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove incident timeline persistence."""

    op.drop_index(
        (
            "ix_incident_timeline_events_"
            "occurred_at"
        ),
        table_name="incident_timeline_events",
    )

    op.drop_index(
        (
            "ix_incident_timeline_events_"
            "actor_id"
        ),
        table_name="incident_timeline_events",
    )

    op.drop_index(
        (
            "ix_incident_timeline_events_"
            "event_type"
        ),
        table_name="incident_timeline_events",
    )

    op.drop_index(
        (
            "ix_incident_timeline_events_"
            "incident_occurred"
        ),
        table_name="incident_timeline_events",
    )

    op.drop_table(
        "incident_timeline_events"
    )