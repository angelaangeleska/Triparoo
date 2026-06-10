"""Add city coordinates

Revision ID: 002
Revises: 001
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cities", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("cities", sa.Column("longitude", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("cities", "longitude")
    op.drop_column("cities", "latitude")
