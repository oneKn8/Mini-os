"""Add preference learning tables

Revision ID: d45678901234
Revises: c12345678901
Create Date: 2025-11-27 08:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d45678901234"
down_revision: Union[str, None] = "c12345678901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Preference profiles - stores per-user risk tolerance and stats
    op.create_table(
        "preference_profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("risk_tolerance", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("total_interactions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("auto_approve_success_rate", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_preference_profiles_user_id"), "preference_profiles", ["user_id"], unique=True)

    # Learned preferences - individual preference signals per user
    op.create_table(
        "learned_preferences",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("profile_id", sa.UUID(), nullable=False),
        sa.Column("preference_type", sa.String(length=100), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("evidence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["profile_id"], ["preference_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_learned_preferences_profile_id"), "learned_preferences", ["profile_id"], unique=False)
    op.create_index(
        op.f("ix_learned_preferences_preference_type"), "learned_preferences", ["preference_type"], unique=False
    )

    # Approval history - tracks all approval decisions for learning
    op.create_table(
        "approval_history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("action_type", sa.String(length=100), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("risk_score", sa.Integer(), nullable=True),
        sa.Column("was_auto_approved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_approval_history_user_id"), "approval_history", ["user_id"], unique=False)
    op.create_index(op.f("ix_approval_history_action_type"), "approval_history", ["action_type"], unique=False)
    op.create_index(op.f("ix_approval_history_approved"), "approval_history", ["approved"], unique=False)

    # Approval pattern stats - pre-aggregated stats per user/action_type
    op.create_table(
        "approval_patterns",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("profile_id", sa.UUID(), nullable=False),
        sa.Column("action_type", sa.String(length=100), nullable=False),
        sa.Column("approved_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["profile_id"], ["preference_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "action_type", name="uix_approval_patterns_profile_action"),
    )
    op.create_index(op.f("ix_approval_patterns_profile_id"), "approval_patterns", ["profile_id"], unique=False)
    op.create_index(op.f("ix_approval_patterns_action_type"), "approval_patterns", ["action_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_approval_patterns_action_type"), table_name="approval_patterns")
    op.drop_index(op.f("ix_approval_patterns_profile_id"), table_name="approval_patterns")
    op.drop_table("approval_patterns")

    op.drop_index(op.f("ix_approval_history_approved"), table_name="approval_history")
    op.drop_index(op.f("ix_approval_history_action_type"), table_name="approval_history")
    op.drop_index(op.f("ix_approval_history_user_id"), table_name="approval_history")
    op.drop_table("approval_history")

    op.drop_index(op.f("ix_learned_preferences_preference_type"), table_name="learned_preferences")
    op.drop_index(op.f("ix_learned_preferences_profile_id"), table_name="learned_preferences")
    op.drop_table("learned_preferences")

    op.drop_index(op.f("ix_preference_profiles_user_id"), table_name="preference_profiles")
    op.drop_table("preference_profiles")
