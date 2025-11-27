"""
Preference Learning Models

SQLAlchemy models for storing user preference profiles, learned preferences,
and approval history for the ML-based preference learning system.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.api.models.base import Base


class PreferenceProfile(Base):
    """User preference profile with risk tolerance and interaction stats."""

    __tablename__ = "preference_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, unique=True, index=True)
    risk_tolerance = Column(Float, nullable=False, default=0.5)
    total_interactions = Column(Integer, nullable=False, default=0)
    auto_approve_success_rate = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    learned_preferences = relationship("LearnedPreference", back_populates="profile", cascade="all, delete-orphan")
    approval_patterns = relationship("ApprovalPattern", back_populates="profile", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PreferenceProfile(user_id={self.user_id}, risk_tolerance={self.risk_tolerance})>"


class LearnedPreference(Base):
    """Individual learned preference for a user."""

    __tablename__ = "learned_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(
        UUID(as_uuid=True), ForeignKey("preference_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    preference_type = Column(String(100), nullable=False, index=True)  # e.g., "email_tone", "meeting_duration"
    value = Column(JSONB, nullable=True)  # The preferred value (can be any JSON type)
    confidence = Column(Float, nullable=False, default=0.5)
    evidence_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship("PreferenceProfile", back_populates="learned_preferences")

    def __repr__(self):
        return f"<LearnedPreference(type={self.preference_type}, value={self.value}, confidence={self.confidence})>"


class ApprovalHistory(Base):
    """History of all approval decisions for learning."""

    __tablename__ = "approval_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    action_type = Column(String(100), nullable=False, index=True)
    approved = Column(Boolean, nullable=False, index=True)
    payload = Column(JSONB, nullable=True)
    risk_score = Column(Integer, nullable=True)
    was_auto_approved = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<ApprovalHistory(action={self.action_type}, approved={self.approved})>"


class ApprovalPattern(Base):
    """Pre-aggregated approval stats per user/action_type."""

    __tablename__ = "approval_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(
        UUID(as_uuid=True), ForeignKey("preference_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action_type = Column(String(100), nullable=False, index=True)
    approved_count = Column(Integer, nullable=False, default=0)
    rejected_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship("PreferenceProfile", back_populates="approval_patterns")

    @property
    def total_count(self) -> int:
        return self.approved_count + self.rejected_count

    @property
    def approval_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.approved_count / self.total_count

    def __repr__(self):
        return f"<ApprovalPattern(action={self.action_type}, rate={self.approval_rate:.2f})>"
