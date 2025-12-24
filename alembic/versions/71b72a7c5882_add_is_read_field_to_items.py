"""add_is_read_field_to_items

Revision ID: 71b72a7c5882
Revises: d45678901234
Create Date: 2025-11-27 23:35:27.160377

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "71b72a7c5882"
down_revision: Union[str, None] = "d45678901234"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_read column to items table
    op.add_column("items", sa.Column("is_read", sa.Boolean(), nullable=True))

    # Set default value for existing rows
    op.execute("UPDATE items SET is_read = false WHERE is_read IS NULL")

    # Make column non-nullable
    op.alter_column("items", "is_read", nullable=False, server_default=sa.false())

    # Add index
    op.create_index("ix_items_is_read", "items", ["is_read"])


def downgrade() -> None:
    # Remove index
    op.drop_index("ix_items_is_read", table_name="items")

    # Remove column
    op.drop_column("items", "is_read")
