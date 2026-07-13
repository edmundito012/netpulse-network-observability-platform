"""add alert deduplication

Revision ID: a4c9e2d71b30
Revises: 51c08eea2f94
Create Date: 2026-07-13 23:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a4c9e2d71b30"
down_revision: str | Sequence[str] | None = "51c08eea2f94"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add functional alert identity and recurrence metadata."""

    op.add_column(
        "alerts",
        sa.Column(
            "alert_type",
            sa.String(length=50),
            nullable=True,
        ),
    )

    op.add_column(
        "alerts",
        sa.Column(
            "deduplication_key",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "alerts",
        sa.Column(
            "occurrence_count",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )

    op.add_column(
        "alerts",
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "alerts",
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE alerts
        SET
            alert_type = 'GENERIC',
            deduplication_key = 'legacy:' || id::text,
            occurrence_count = 1,
            first_seen_at = created_at,
            last_seen_at = created_at
        """
    )

    op.alter_column(
        "alerts",
        "alert_type",
        existing_type=sa.String(length=50),
        nullable=False,
    )

    op.alter_column(
        "alerts",
        "deduplication_key",
        existing_type=sa.String(length=255),
        nullable=False,
    )

    op.alter_column(
        "alerts",
        "first_seen_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )

    op.alter_column(
        "alerts",
        "last_seen_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )

    op.create_index(
        "ix_alerts_device_id_deduplication_key",
        "alerts",
        [
            "device_id",
            "deduplication_key",
        ],
        unique=False,
    )

    op.create_index(
        "ix_alerts_alert_type",
        "alerts",
        ["alert_type"],
        unique=False,
    )

    op.create_index(
        "uq_alerts_active_deduplication",
        "alerts",
        [
            "device_id",
            "deduplication_key",
        ],
        unique=True,
        postgresql_where=sa.text(
            "status IN ('OPEN', 'ACKNOWLEDGED')"
        ),
    )

    op.alter_column(
        "alerts",
        "occurrence_count",
        server_default=None,
    )


def downgrade() -> None:
    """Remove alert deduplication metadata."""

    op.drop_index(
        "uq_alerts_active_deduplication",
        table_name="alerts",
    )

    op.drop_index(
        "ix_alerts_alert_type",
        table_name="alerts",
    )

    op.drop_index(
        "ix_alerts_device_id_deduplication_key",
        table_name="alerts",
    )

    op.drop_column(
        "alerts",
        "last_seen_at",
    )

    op.drop_column(
        "alerts",
        "first_seen_at",
    )

    op.drop_column(
        "alerts",
        "occurrence_count",
    )

    op.drop_column(
        "alerts",
        "deduplication_key",
    )

    op.drop_column(
        "alerts",
        "alert_type",
    )