"""
Action proposal and execution models.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.api.models.base import Base, TimestampMixin, UUIDMixin


class ActionProposal(Base, UUIDMixin, TimestampMixin):
    """Agent-proposed actions awaiting user approval."""

    __tablename__ = "action_proposals"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    related_item_id = Column(UUID(as_uuid=True), ForeignKey("items.id", ondelete="SET NULL"))
    agent_name = Column(String(100), nullable=False)
    action_type = Column(String(100), nullable=False)  # create_email_draft, create_calendar_event, etc.
    payload = Column(JSONB, nullable=False)
    status = Column(
        String(50), default="pending", index=True
    )  # pending, approved, executed, rejected, failed, expired
    risk_level = Column(String(50), default="low")  # low, medium, high
    explanation = Column(Text)
    warning_text = Column(Text)
    expires_at = Column(DateTime, index=True)
    approved_at = Column(DateTime)
    executed_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="action_proposals")
    related_item = relationship("Item", back_populates="action_proposals")
    execution_log = relationship(
        "ExecutionLog", back_populates="action_proposal", uselist=False, cascade="all, delete-orphan"
    )
    preference_signals = relationship("PreferenceSignal", back_populates="action_proposal")

    def __repr__(self):
        return f"<ActionProposal(id={self.id}, type={self.action_type}, status={self.status})>"


class ExecutionLog(Base, UUIDMixin, TimestampMixin):
    """Logs of executed actions."""

    __tablename__ = "execution_logs"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action_proposal_id = Column(
        UUID(as_uuid=True), ForeignKey("action_proposals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    executor_status = Column(String(50), nullable=False, index=True)  # success, failure, partial
    executor_error = Column(Text)
    external_ids = Column(JSONB)  # Provider IDs (draft_id, event_id, etc.)
    request_payload = Column(JSONB)
    response_payload = Column(JSONB)
    execution_duration_ms = Column(Integer)

    # Relationships
    user = relationship("User")
    action_proposal = relationship("ActionProposal", back_populates="execution_log")

    def __repr__(self):
        return f"<ExecutionLog(id={self.id}, status={self.executor_status})>"


class PreferenceSignal(Base, UUIDMixin, TimestampMixin):
    """Tracks user interactions for learning preferences."""

    __tablename__ = "preference_signals"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id", ondelete="SET NULL"))
    action_proposal_id = Column(UUID(as_uuid=True), ForeignKey("action_proposals.id", ondelete="SET NULL"), index=True)
    signal_type = Column(String(50), nullable=False, index=True)  # approved, rejected, ignored, edited_heavily, etc.
    context = Column(JSONB)

    # Relationships
    user = relationship("User", back_populates="preference_signals")
    item = relationship("Item", back_populates="preference_signals")
    action_proposal = relationship("ActionProposal", back_populates="preference_signals")

    def __repr__(self):
        return f"<PreferenceSignal(id={self.id}, type={self.signal_type})>"
