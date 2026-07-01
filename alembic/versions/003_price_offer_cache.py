"""Add flight and hotel offer cache tables for offline testing

Revision ID: 003
Revises: 002
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "flight_offer_cache",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("origin_iata", sa.String(length=3), nullable=False),
        sa.Column("destination_iata", sa.String(length=3), nullable=False),
        sa.Column("departure_date", sa.Date(), nullable=False),
        sa.Column("return_date", sa.Date(), nullable=True),
        sa.Column("party_size", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_flight_offer_cache_route",
        "flight_offer_cache",
        ["origin_iata", "destination_iata", "departure_date"],
    )

    op.create_table(
        "hotel_offer_cache",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("country", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("check_in", sa.Date(), nullable=True),
        sa.Column("check_out", sa.Date(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hotel_offer_cache_city", "hotel_offer_cache", ["city", "country"])


def downgrade() -> None:
    op.drop_index("ix_hotel_offer_cache_city", table_name="hotel_offer_cache")
    op.drop_table("hotel_offer_cache")
    op.drop_index("ix_flight_offer_cache_route", table_name="flight_offer_cache")
    op.drop_table("flight_offer_cache")
