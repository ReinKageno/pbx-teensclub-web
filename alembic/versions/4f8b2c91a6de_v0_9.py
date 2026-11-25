"""Add transaction modifier user ID.

Revision ID: 4f8b2c91a6de
Revises: 1c65244f87eb
Create Date: 2026-11-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4f8b2c91a6de"
down_revision: Union[str, Sequence[str], None] = "1c65244f87eb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("last_modified_by_user_id", sa.String(), nullable=True),
        schema="economy_donation",
    )


def downgrade() -> None:
    op.drop_column(
        "transactions",
        "last_modified_by_user_id",
        schema="economy_donation",
    )
