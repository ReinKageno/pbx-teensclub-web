"""Add optional account identity to transaction issuers.

Revision ID: 98c2e14a7d31
Revises: 4f8b2c91a6de
Create Date: 2026-11-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "98c2e14a7d31"
down_revision: Union[str, Sequence[str], None] = "4f8b2c91a6de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_server_user_user_id",
        "user",
        ["user_id"],
        schema="server",
    )
    op.add_column(
        "transactions",
        sa.Column("issuer_user_id", sa.String(), nullable=True),
        schema="economy_donation",
    )
    op.create_foreign_key(
        "fk_transactions_issuer_user_id_user",
        "transactions",
        "user",
        ["issuer_user_id"],
        ["user_id"],
        source_schema="economy_donation",
        referent_schema="server",
    )
    op.create_index(
        "ix_transactions_issuer_user_id",
        "transactions",
        ["issuer_user_id"],
        schema="economy_donation",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_transactions_issuer_user_id_user",
        "transactions",
        schema="economy_donation",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_transactions_issuer_user_id",
        table_name="transactions",
        schema="economy_donation",
    )
    op.drop_column(
        "transactions",
        "issuer_user_id",
        schema="economy_donation",
    )
    op.drop_constraint(
        "uq_server_user_user_id",
        "user",
        schema="server",
        type_="unique",
    )
