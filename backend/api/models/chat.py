"""
Chat session and message models for persisting conversations.
"""

from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.api.models.base import Base, TimestampMixin, UUIDMixin


class ChatSession(Base, UUIDMixin, TimestampMixin):
    """Stores metadata about a chat session."""

    __tablename__ = "chat_sessions"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(200), nullable=True)  # Generated from first message
    status = Column(String(20), default="active")
    session_metadata = Column("metadata", JSONB)

    messages = relationship("ChatMessageEntry", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, title={self.title}, status={self.status})>"


class ChatMessageEntry(Base, UUIDMixin, TimestampMixin):
    """Persists individual chat messages for a session."""

    __tablename__ = "chat_messages"

    session_id = Column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender = Column(String(20), nullable=False)  # user or assistant
    content = Column(Text, nullable=False)
    message_metadata = Column("metadata", JSONB)

    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessageEntry(id={self.id}, sender={self.sender})>"
