"""v0.8

Revision ID: 1c65244f87eb
Revises: 9d33d1c4dc03
Create Date: 2026-11-24 13:32:34.349784

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1c65244f87eb'
down_revision: Union[str, Sequence[str], None] = '9d33d1c4dc03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE server.notifytype RENAME TO notifylevel")
    op.execute("ALTER TYPE economy_donation.transactiontype RENAME TO transactionio")

    op.alter_column("notifications", "type", new_column_name="level", schema="server")
    op.alter_column("transactions", "flow", new_column_name="io", schema="economy_donation")
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("notifications", "level", new_column_name="type", schema="server")
    op.alter_column("transactions", "io", new_column_name="type", schema="economy_donation")

    op.execute("ALTER TYPE server.notifylevel RENAME TO notifytype")
    op.execute("ALTER TYPE economy_donation.transactionio RENAME TO transactiontype")
    pass
