"""
Item and item metadata models.
"""

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.api.models.base import Base, TimestampMixin, UUIDMixin


class Item(Base, UUIDMixin, TimestampMixin):
    """Normalized storage for emails and calendar events."""

    __tablename__ = "items"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)  # email, event
    source_provider = Column(String(50), nullable=False)  # gmail, outlook, google_calendar
    source_account_id = Column(UUID(as_uuid=True), ForeignKey("connected_accounts.id", ondelete="SET NULL"))
    source_id = Column(String(255), nullable=False)  # Provider's ID
    thread_id = Column(String(255), index=True)  # Conversation/thread identifier (e.g., Gmail threadId)
    title = Column(String(500))
    body_preview = Column(Text)
    body_full = Column(Text)
    sender = Column(String(255))
    recipients = Column(JSONB)  # Array of email addresses
    start_datetime = Column(DateTime, index=True)
    end_datetime = Column(DateTime)
    received_datetime = Column(DateTime, index=True)
    raw_metadata = Column(JSONB)
    is_read = Column(Boolean, default=False, index=True)
    is_archived = Column(Boolean, default=False, index=True)

    # Relationships
    user = relationship("User", back_populates="items")
    source_account = relationship("ConnectedAccount", back_populates="items")
    agent_metadata = relationship(
        "ItemAgentMetadata", back_populates="item", uselist=False, cascade="all, delete-orphan"
    )
    action_proposals = relationship("ActionProposal", back_populates="related_item")
    preference_signals = relationship("PreferenceSignal", back_populates="item")

    def __repr__(self):
        return f"<Item(id={self.id}, type={self.source_type}, provider={self.source_provider})>"


class ItemAgentMetadata(Base, TimestampMixin):
    """Agent-generated metadata for items."""

    __tablename__ = "item_agent_metadata"

    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    category = Column(String(50), index=True)  # deadline, meeting, invite, admin, etc.
    importance = Column(String(50), index=True)  # critical, high, medium, low, ignore
    action_type = Column(String(50))  # reply, attend, add_event, pay, read, none
    due_datetime = Column(DateTime, index=True)
    confidence_score = Column(Float)
    labels = Column(JSONB)  # Array of extracted entities
    is_scam = Column(Boolean, default=False, index=True)
    is_noise = Column(Boolean, default=False)
    summary = Column(Text)

    # Relationships
    item = relationship("Item", back_populates="agent_metadata")

    def __repr__(self):
        return f"<ItemAgentMetadata(item_id={self.item_id}, category={self.category}, importance={self.importance})>"
