"""add thread_id to items

Revision ID: 8c1e3c3c1c1b
Revises: 71b72a7c5882
Create Date: 2024-11-28
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8c1e3c3c1c1b'
down_revision = '71b72a7c5882'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('items', sa.Column('thread_id', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_items_thread_id'), 'items', ['thread_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_items_thread_id'), table_name='items')
    op.drop_column('items', 'thread_id')
