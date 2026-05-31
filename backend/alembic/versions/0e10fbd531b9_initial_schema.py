"""initial schema

Revision ID: 0e10fbd531b9
Revises:
Create Date: 2026-05-14 02:13:43.691530

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0e10fbd531b9"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_role_enum = sa.Enum(
        "ADMIN",
        "OPERATOR",
        "VIEWER",
        name="userrole",
    )

    device_status_enum = sa.Enum(
        "ONLINE",
        "OFFLINE",
        "UNKNOWN",
        name="devicestatus",
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("ip_address", sa.String(), nullable=False),
        sa.Column("hostname", sa.String(), nullable=True),
        sa.Column("device_type", sa.String(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("status", device_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_devices_id"), "devices", ["id"], unique=False)
    op.create_index(op.f("ix_devices_ip_address"), "devices", ["ip_address"], unique=True)

    op.create_table(
        "device_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("status", device_status_enum, nullable=False),
        sa.Column("response_time_ms", sa.Float(), nullable=True),
        sa.Column("checked_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_device_metrics_id"), "device_metrics", ["id"], unique=False)
    op.create_index(op.f("ix_device_metrics_device_id"), "device_metrics", ["device_id"], unique=False)
    op.create_index(op.f("ix_device_metrics_checked_at"), "device_metrics", ["checked_at"], unique=False)

    op.create_table(
        "device_snmp_system_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("sysdescr", sa.String(), nullable=True),
        sa.Column("sysuptime", sa.String(), nullable=True),
        sa.Column("syscontact", sa.String(), nullable=True),
        sa.Column("sysname", sa.String(), nullable=True),
        sa.Column("syslocation", sa.String(), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_device_snmp_system_snapshots_id"),
        "device_snmp_system_snapshots",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_device_snmp_system_snapshots_device_id"),
        "device_snmp_system_snapshots",
        ["device_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_device_snmp_system_snapshots_device_id"), table_name="device_snmp_system_snapshots")
    op.drop_index(op.f("ix_device_snmp_system_snapshots_id"), table_name="device_snmp_system_snapshots")
    op.drop_table("device_snmp_system_snapshots")

    op.drop_index(op.f("ix_device_metrics_checked_at"), table_name="device_metrics")
    op.drop_index(op.f("ix_device_metrics_device_id"), table_name="device_metrics")
    op.drop_index(op.f("ix_device_metrics_id"), table_name="device_metrics")
    op.drop_table("device_metrics")

    op.drop_index(op.f("ix_devices_ip_address"), table_name="devices")
    op.drop_index(op.f("ix_devices_id"), table_name="devices")
    op.drop_table("devices")

    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")

    sa.Enum(name="devicestatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="userrole").drop(op.get_bind(), checkfirst=True)