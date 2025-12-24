"""Add title column to chat_sessions

Revision ID: c12345678901
Revises: b78625017de4
Create Date: 2024-11-26

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c12345678901"
down_revision = "b78625017de4"
branch_labels = None
depends_on = None


def upgrade():
    # Add title column to chat_sessions table
    op.add_column("chat_sessions", sa.Column("title", sa.String(200), nullable=True))


def downgrade():
    op.drop_column("chat_sessions", "title")
