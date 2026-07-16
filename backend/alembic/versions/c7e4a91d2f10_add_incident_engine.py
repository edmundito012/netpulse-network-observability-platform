"""add incident engine

Revision ID: c7e4a91d2f10
Revises: a4c9e2d71b30
Create Date: 2026-07-16 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c7e4a91d2f10"
down_revision: str | Sequence[str] | None = (
    "a4c9e2d71b30"
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create incident persistence and alert associations."""

    op.execute(
        """
        CREATE SEQUENCE incident_public_id_seq
        START WITH 1
        INCREMENT BY 1
        NO MINVALUE
        NO MAXVALUE
        CACHE 1
        """
    )

    op.create_table(
        "incidents",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "public_id",
            sa.String(length=32),
            server_default=sa.text(
                "'INC-' || "
                "to_char(CURRENT_DATE, 'YYYY') || "
                "'-' || "
                "lpad("
                "nextval('incident_public_id_seq')::text, "
                "6, "
                "'0'"
                ")"
            ),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="OPEN",
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.String(length=32),
            server_default="WARNING",
            nullable=False,
        ),
        sa.Column(
            "priority",
            sa.String(length=32),
            server_default="MEDIUM",
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.String(length=32),
            server_default="MANUAL",
            nullable=False,
        ),
        sa.Column(
            "owner_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "business_impact",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "root_cause",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "resolution_summary",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "tags",
            sa.JSON(),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
        sa.Column(
            "metadata",
            sa.JSON(),
            server_default=sa.text("'{}'::json"),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "acknowledged_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "resolved_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ("
            "'OPEN', "
            "'ACKNOWLEDGED', "
            "'INVESTIGATING', "
            "'MONITORING', "
            "'RESOLVED'"
            ")",
            name="ck_incidents_status",
        ),
        sa.CheckConstraint(
            "severity IN ("
            "'INFO', "
            "'WARNING', "
            "'CRITICAL'"
            ")",
            name="ck_incidents_severity",
        ),
        sa.CheckConstraint(
            "priority IN ("
            "'LOW', "
            "'MEDIUM', "
            "'HIGH', "
            "'CRITICAL'"
            ")",
            name="ck_incidents_priority",
        ),
        sa.CheckConstraint(
            "source IN ("
            "'MANUAL', "
            "'API', "
            "'ALERT_ENGINE', "
            "'CORRELATION_ENGINE', "
            "'ROOT_CAUSE_ENGINE'"
            ")",
            name="ck_incidents_source",
        ),
        sa.CheckConstraint(
            "resolved_at IS NULL "
            "OR status = 'RESOLVED'",
            name="ck_incidents_resolution_status",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name="fk_incidents_owner_id_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_incidents",
        ),
        sa.UniqueConstraint(
            "public_id",
            name="uq_incidents_public_id",
        ),
    )

    op.create_index(
        "ix_incidents_public_id",
        "incidents",
        ["public_id"],
        unique=True,
    )

    op.create_index(
        "ix_incidents_owner_id",
        "incidents",
        ["owner_id"],
        unique=False,
    )

    op.create_index(
        "ix_incidents_status",
        "incidents",
        ["status"],
        unique=False,
    )

    op.create_index(
        "ix_incidents_severity",
        "incidents",
        ["severity"],
        unique=False,
    )

    op.create_index(
        "ix_incidents_priority",
        "incidents",
        ["priority"],
        unique=False,
    )

    op.create_index(
        "ix_incidents_owner_id_status",
        "incidents",
        [
            "owner_id",
            "status",
        ],
        unique=False,
    )

    op.create_index(
        "ix_incidents_detected_at",
        "incidents",
        ["detected_at"],
        unique=False,
    )

    op.create_index(
        "ix_incidents_status_detected_at",
        "incidents",
        [
            "status",
            "detected_at",
        ],
        unique=False,
    )

    op.create_table(
        "incident_alerts",
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
            "alert_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "attached_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["alert_id"],
            ["alerts.id"],
            name="fk_incident_alerts_alert_id_alerts",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["incidents.id"],
            name=(
                "fk_incident_alerts_incident_id_"
                "incidents"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_incident_alerts",
        ),
        sa.UniqueConstraint(
            "alert_id",
            name="uq_incident_alerts_alert_id",
        ),
    )

    op.create_index(
        "ix_incident_alerts_incident_id",
        "incident_alerts",
        ["incident_id"],
        unique=False,
    )

    op.create_index(
        "ix_incident_alerts_attached_at",
        "incident_alerts",
        ["attached_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove incident persistence and public identifier sequence."""

    op.drop_index(
        "ix_incident_alerts_attached_at",
        table_name="incident_alerts",
    )

    op.drop_index(
        "ix_incident_alerts_incident_id",
        table_name="incident_alerts",
    )

    op.drop_table("incident_alerts")

    op.drop_index(
        "ix_incidents_status_detected_at",
        table_name="incidents",
    )

    op.drop_index(
        "ix_incidents_detected_at",
        table_name="incidents",
    )

    op.drop_index(
        "ix_incidents_owner_id_status",
        table_name="incidents",
    )

    op.drop_index(
        "ix_incidents_priority",
        table_name="incidents",
    )

    op.drop_index(
        "ix_incidents_severity",
        table_name="incidents",
    )

    op.drop_index(
        "ix_incidents_status",
        table_name="incidents",
    )

    op.drop_index(
        "ix_incidents_owner_id",
        table_name="incidents",
    )

    op.drop_index(
        "ix_incidents_public_id",
        table_name="incidents",
    )

    op.drop_table("incidents")

    op.execute(
        "DROP SEQUENCE incident_public_id_seq"
    )