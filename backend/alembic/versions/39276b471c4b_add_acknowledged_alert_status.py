"""add acknowledged alert status

Revision ID: 39276b471c4b
Revises: 5463f00259b7
Create Date: 2026-05-14 23:57:24.102955

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "39276b471c4b"
down_revision: Union[str, Sequence[str], None] = "5463f00259b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE alertstatus ADD VALUE IF NOT EXISTS 'ACKNOWLEDGED';"
    )


def downgrade() -> None:
    pass