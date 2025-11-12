"""
Agent run log model.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.api.models.base import Base, TimestampMixin, UUIDMixin


class AgentRunLog(Base, UUIDMixin, TimestampMixin):
    """Logs of orchestrator and agent executions."""

    __tablename__ = "agent_run_logs"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)  # orchestrator, triage, email, planner, etc.
    context = Column(String(100), nullable=False)  # refresh_inbox, plan_day, handle_item, etc.
    input_summary = Column(JSONB)
    output_summary = Column(JSONB)
    status = Column(String(50), nullable=False, index=True)  # success, partial, error
    error_message = Column(Text)
    duration_ms = Column(Integer)
    completed_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="agent_run_logs")

    def __repr__(self):
        return f"<AgentRunLog(id={self.id}, agent={self.agent_name}, status={self.status})>"
