"""
User-related database models.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.api.models.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    """User account model."""

    __tablename__ = "users"

    email = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(255))
    password_hash = Column(String(255), nullable=False)
    timezone = Column(String(50), default="UTC")
    location_city = Column(String(100))
    location_country = Column(String(100))
    is_active = Column(Boolean, default=True, index=True)
    last_login_at = Column(DateTime)

    # Relationships
    connected_accounts = relationship("ConnectedAccount", back_populates="user", cascade="all, delete-orphan")
    items = relationship("Item", back_populates="user", cascade="all, delete-orphan")
    action_proposals = relationship("ActionProposal", back_populates="user", cascade="all, delete-orphan")
    agent_run_logs = relationship("AgentRunLog", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preference_signals = relationship("PreferenceSignal", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class ConnectedAccount(Base, UUIDMixin, TimestampMixin):
    """OAuth-connected external accounts."""

    __tablename__ = "connected_accounts"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # gmail, outlook, google_calendar
    provider_account_id = Column(String(255))
    provider_email = Column(String(255))
    access_token = Column(Text, nullable=False)  # Encrypted
    refresh_token = Column(Text)  # Encrypted
    token_expires_at = Column(DateTime, index=True)
    scopes = Column(JSONB)
    status = Column(String(50), default="active", index=True)  # active, expired, revoked, error
    last_sync_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="connected_accounts")
    items = relationship("Item", back_populates="source_account")

    def __repr__(self):
        return f"<ConnectedAccount(id={self.id}, provider={self.provider}, user_id={self.user_id})>"


class UserPreferences(Base, TimestampMixin):
    """User preferences and settings."""

    __tablename__ = "user_preferences"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    quiet_hours_start = Column(String(5))  # HH:MM format
    quiet_hours_end = Column(String(5))  # HH:MM format
    preferred_work_blocks = Column(JSONB)  # Array of {day, start, end}
    email_tone = Column(String(50), default="professional")  # casual, friendly, professional, formal
    meeting_preferences = Column(JSONB)
    auto_reject_high_risk = Column(Boolean, default=True)
    enable_safety_agent = Column(Boolean, default=True)
    enable_preference_learning = Column(Boolean, default=True)
    notification_settings = Column(JSONB)

    # Relationships
    user = relationship("User", back_populates="preferences")

    def __repr__(self):
        return f"<UserPreferences(user_id={self.user_id})>"
