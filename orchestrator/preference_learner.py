"""
Preference Learning System for Personalized Agent Behavior.

Learns from user decisions to improve future predictions and reduce approval fatigue.
Now with database persistence for learned preferences.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class UserPreference:
    """Learned preference for a user."""

    preference_type: str  # e.g., "email_tone", "meeting_duration", "auto_approve_drafts"
    value: Any  # The preferred value
    confidence: float  # 0.0-1.0
    evidence_count: int  # Number of supporting decisions
    last_updated: datetime


@dataclass
class PreferenceProfile:
    """Complete preference profile for a user."""

    user_id: str
    preferences: Dict[str, UserPreference] = field(default_factory=dict)
    risk_tolerance: float = 0.5  # 0.0 (conservative) to 1.0 (aggressive)
    approval_patterns: Dict[str, Dict[str, int]] = field(
        default_factory=lambda: defaultdict(lambda: {"approved": 0, "rejected": 0})
    )
    total_interactions: int = 0
    auto_approve_success_rate: float = 0.0  # For actions that were auto-approved

    def get_preference(self, preference_type: str) -> Optional[UserPreference]:
        """Get a specific preference."""
        return self.preferences.get(preference_type)

    def set_preference(self, pref: UserPreference):
        """Set or update a preference."""
        self.preferences[pref.preference_type] = pref
        pref.last_updated = datetime.now()


class PreferenceEngine:
    """
    Machine learning engine for user preference discovery.

    Learns from:
    1. Approval/rejection patterns
    2. Time of day preferences
    3. Content style preferences
    4. Risk tolerance
    5. Tool usage patterns

    Outputs:
    - Personalized risk thresholds
    - Preferred action strategies
    - Auto-approve confidence adjustments

    Now with optional database persistence.
    """

    def __init__(self, db: Optional[Session] = None):
        """Initialize preference engine with optional database session."""
        self.db = db
        # In-memory cache (also used as fallback when no DB)
        self._profiles_cache: Dict[str, PreferenceProfile] = {}
        self.global_stats = {
            "total_approvals": 0,
            "total_rejections": 0,
            "auto_approved_success": 0,
            "auto_approved_complaints": 0,
        }

    def set_db(self, db: Session):
        """Set database session for persistence."""
        self.db = db

    def get_or_create_profile(self, user_id: str) -> PreferenceProfile:
        """Get or create user preference profile (with DB persistence)."""
        # Check cache first
        if user_id in self._profiles_cache:
            return self._profiles_cache[user_id]

        # Try to load from database
        if self.db:
            try:
                profile = self._load_profile_from_db(user_id)
                if profile:
                    self._profiles_cache[user_id] = profile
                    return profile
            except Exception as e:
                logger.warning(f"Failed to load profile from DB: {e}")

        # Create new profile
        profile = PreferenceProfile(user_id=user_id)
        self._profiles_cache[user_id] = profile

        # Persist to DB
        if self.db:
            try:
                self._save_profile_to_db(profile)
            except Exception as e:
                logger.warning(f"Failed to save profile to DB: {e}")

        logger.info(f"Created new preference profile for user {user_id}")
        return profile

    def _load_profile_from_db(self, user_id: str) -> Optional[PreferenceProfile]:
        """Load profile from database."""
        from backend.api.models.preference_learning import (
            PreferenceProfile as DBPreferenceProfile,
        )

        db_profile = self.db.query(DBPreferenceProfile).filter(DBPreferenceProfile.user_id == user_id).first()

        if not db_profile:
            return None

        # Build profile from DB
        profile = PreferenceProfile(
            user_id=user_id,
            risk_tolerance=db_profile.risk_tolerance,
            total_interactions=db_profile.total_interactions,
            auto_approve_success_rate=db_profile.auto_approve_success_rate or 0.0,
        )

        # Load learned preferences
        for lp in db_profile.learned_preferences:
            profile.preferences[lp.preference_type] = UserPreference(
                preference_type=lp.preference_type,
                value=lp.value,
                confidence=lp.confidence,
                evidence_count=lp.evidence_count,
                last_updated=lp.updated_at,
            )

        # Load approval patterns
        for ap in db_profile.approval_patterns:
            profile.approval_patterns[ap.action_type] = {
                "approved": ap.approved_count,
                "rejected": ap.rejected_count,
            }

        return profile

    def _save_profile_to_db(self, profile: PreferenceProfile):
        """Save profile to database."""
        from backend.api.models.preference_learning import (
            PreferenceProfile as DBPreferenceProfile,
            LearnedPreference,
            ApprovalPattern,
        )
        import uuid

        # Check if profile exists
        db_profile = self.db.query(DBPreferenceProfile).filter(DBPreferenceProfile.user_id == profile.user_id).first()

        if not db_profile:
            # Create new
            db_profile = DBPreferenceProfile(
                id=uuid.uuid4(),
                user_id=profile.user_id,
                risk_tolerance=profile.risk_tolerance,
                total_interactions=profile.total_interactions,
                auto_approve_success_rate=profile.auto_approve_success_rate,
            )
            self.db.add(db_profile)
            self.db.flush()
        else:
            # Update existing
            db_profile.risk_tolerance = profile.risk_tolerance
            db_profile.total_interactions = profile.total_interactions
            db_profile.auto_approve_success_rate = profile.auto_approve_success_rate
            db_profile.updated_at = datetime.utcnow()

        # Update learned preferences
        for pref_type, pref in profile.preferences.items():
            db_pref = (
                self.db.query(LearnedPreference)
                .filter(LearnedPreference.profile_id == db_profile.id, LearnedPreference.preference_type == pref_type)
                .first()
            )

            if not db_pref:
                db_pref = LearnedPreference(
                    id=uuid.uuid4(),
                    profile_id=db_profile.id,
                    preference_type=pref_type,
                    value=pref.value,
                    confidence=pref.confidence,
                    evidence_count=pref.evidence_count,
                )
                self.db.add(db_pref)
            else:
                db_pref.value = pref.value
                db_pref.confidence = pref.confidence
                db_pref.evidence_count = pref.evidence_count
                db_pref.updated_at = datetime.utcnow()

        # Update approval patterns
        for action_type, patterns in profile.approval_patterns.items():
            db_pattern = (
                self.db.query(ApprovalPattern)
                .filter(ApprovalPattern.profile_id == db_profile.id, ApprovalPattern.action_type == action_type)
                .first()
            )

            if not db_pattern:
                db_pattern = ApprovalPattern(
                    id=uuid.uuid4(),
                    profile_id=db_profile.id,
                    action_type=action_type,
                    approved_count=patterns["approved"],
                    rejected_count=patterns["rejected"],
                )
                self.db.add(db_pattern)
            else:
                db_pattern.approved_count = patterns["approved"]
                db_pattern.rejected_count = patterns["rejected"]
                db_pattern.updated_at = datetime.utcnow()

        self.db.commit()

    def _record_approval_history(
        self,
        user_id: str,
        action_type: str,
        approved: bool,
        payload: Dict,
        risk_score: Optional[int],
        was_auto_approved: bool,
    ):
        """Record approval in history table."""
        if not self.db:
            return

        try:
            from backend.api.models.preference_learning import ApprovalHistory
            import uuid

            history = ApprovalHistory(
                id=uuid.uuid4(),
                user_id=user_id,
                action_type=action_type,
                approved=approved,
                payload=payload,
                risk_score=risk_score,
                was_auto_approved=was_auto_approved,
            )
            self.db.add(history)
            self.db.commit()
        except Exception as e:
            logger.warning(f"Failed to record approval history: {e}")

    def record_decision(
        self,
        user_id: str,
        action_type: str,
        approved: bool,
        payload: Dict,
        was_auto_approved: bool = False,
        risk_score: Optional[int] = None,
    ):
        """
        Record a user decision to learn preferences.

        Args:
            user_id: User ID
            action_type: Type of action
            approved: Whether approved
            payload: Action payload
            was_auto_approved: If this was auto-approved
            risk_score: Risk score from assessment
        """
        profile = self.get_or_create_profile(user_id)

        # Update approval patterns
        profile.approval_patterns[action_type]["approved" if approved else "rejected"] += 1
        profile.total_interactions += 1

        # Update global stats
        if was_auto_approved:
            if approved:
                self.global_stats["auto_approved_success"] += 1
            else:
                self.global_stats["auto_approved_complaints"] += 1
        else:
            if approved:
                self.global_stats["total_approvals"] += 1
            else:
                self.global_stats["total_rejections"] += 1

        # Learn specific preferences
        self._learn_from_decision(profile, action_type, approved, payload, risk_score)

        # Update risk tolerance
        self._update_risk_tolerance(profile)

        # Persist to database
        if self.db:
            try:
                self._save_profile_to_db(profile)
                self._record_approval_history(user_id, action_type, approved, payload, risk_score, was_auto_approved)
            except Exception as e:
                logger.warning(f"Failed to persist decision: {e}")

        logger.info(
            f"Recorded decision for {user_id}: {action_type} -> "
            f"{'approved' if approved else 'rejected'} "
            f"(auto: {was_auto_approved})"
        )

    def _learn_from_decision(
        self,
        profile: PreferenceProfile,
        action_type: str,
        approved: bool,
        payload: Dict,
        risk_score: Optional[int],
    ):
        """Learn specific preferences from a decision."""

        # Learn email tone preferences
        if action_type in ["create_email_draft", "send_email"] and "body" in payload:
            self._learn_email_tone(profile, payload["body"], approved)

        # Learn meeting duration preferences
        if action_type == "create_calendar_event" and "start_time" in payload and "end_time" in payload:
            self._learn_meeting_duration(profile, payload, approved)

        # Learn auto-approval comfort level
        if risk_score is not None:
            self._learn_risk_comfort(profile, risk_score, approved)

        # Learn time-of-day patterns
        self._learn_time_patterns(profile, action_type, approved)

    def _learn_email_tone(self, profile: PreferenceProfile, body: str, approved: bool):
        """Learn email tone preferences (formal vs casual)."""
        if not approved:
            return  # Only learn from approvals

        # Simple heuristics for tone detection
        formal_indicators = [
            "dear",
            "sincerely",
            "regards",
            "respectfully",
            "thank you for your time",
            "i hope this email finds you well",
        ]
        casual_indicators = ["hey", "hi there", "thanks", "cheers", "talk soon", "let me know", "quick question"]

        body_lower = body.lower()

        formal_count = sum(1 for indicator in formal_indicators if indicator in body_lower)
        casual_count = sum(1 for indicator in casual_indicators if indicator in body_lower)

        if formal_count > casual_count and formal_count >= 2:
            tone = "formal"
        elif casual_count > formal_count and casual_count >= 2:
            tone = "casual"
        else:
            return  # Ambiguous, don't learn

        # Update or create preference
        pref_type = "email_tone"
        if pref_type in profile.preferences:
            pref = profile.preferences[pref_type]
            if pref.value == tone:
                pref.evidence_count += 1
                pref.confidence = min(pref.confidence + 0.05, 1.0)
            else:
                # Conflicting preference, reduce confidence
                pref.confidence = max(pref.confidence - 0.1, 0.3)
        else:
            profile.set_preference(
                UserPreference(
                    preference_type=pref_type,
                    value=tone,
                    confidence=0.6,
                    evidence_count=1,
                    last_updated=datetime.now(),
                )
            )

    def _learn_meeting_duration(self, profile: PreferenceProfile, payload: Dict, approved: bool):
        """Learn preferred meeting duration."""
        if not approved:
            return

        try:
            start = datetime.fromisoformat(payload["start_time"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(payload["end_time"].replace("Z", "+00:00"))
            duration_minutes = int((end - start).total_seconds() / 60)

            # Categorize duration
            if duration_minutes <= 15:
                duration_pref = "short"  # 15 min or less
            elif duration_minutes <= 30:
                duration_pref = "standard"  # 30 min
            elif duration_minutes <= 60:
                duration_pref = "long"  # 1 hour
            else:
                duration_pref = "extended"  # Over 1 hour

            pref_type = "meeting_duration"
            if pref_type in profile.preferences:
                pref = profile.preferences[pref_type]
                if pref.value == duration_pref:
                    pref.evidence_count += 1
                    pref.confidence = min(pref.confidence + 0.05, 1.0)
            else:
                profile.set_preference(
                    UserPreference(
                        preference_type=pref_type,
                        value=duration_pref,
                        confidence=0.5,
                        evidence_count=1,
                        last_updated=datetime.now(),
                    )
                )

        except Exception as e:
            logger.warning(f"Failed to learn meeting duration: {e}")

    def _learn_risk_comfort(self, profile: PreferenceProfile, risk_score: int, approved: bool):
        """Learn user's comfort with different risk levels."""
        # If user approved a high-risk action, they're more risk-tolerant
        # If user rejected a low-risk action, they're more conservative

        if approved and risk_score >= 50:
            # User is comfortable with higher risk
            profile.risk_tolerance = min(profile.risk_tolerance + 0.02, 1.0)
        elif not approved and risk_score <= 30:
            # User is more conservative
            profile.risk_tolerance = max(profile.risk_tolerance - 0.02, 0.0)

    def _learn_time_patterns(self, profile: PreferenceProfile, action_type: str, approved: bool):
        """Learn time-of-day patterns (future enhancement)."""
        # This could learn when user prefers certain actions
        # For now, just a placeholder

    def _update_risk_tolerance(self, profile: PreferenceProfile):
        """Update overall risk tolerance based on approval patterns."""
        if profile.total_interactions < 5:
            return  # Not enough data

        # Calculate approval rate across all actions
        total_approved = sum(patterns["approved"] for patterns in profile.approval_patterns.values())
        total_rejected = sum(patterns["rejected"] for patterns in profile.approval_patterns.values())

        if total_approved + total_rejected == 0:
            return

        approval_rate = total_approved / (total_approved + total_rejected)

        # High approval rate (>80%) suggests high risk tolerance
        if approval_rate > 0.8:
            profile.risk_tolerance = min(profile.risk_tolerance + 0.01, 1.0)
        # Low approval rate (<50%) suggests low risk tolerance
        elif approval_rate < 0.5:
            profile.risk_tolerance = max(profile.risk_tolerance - 0.01, 0.0)

    def get_adjusted_risk_threshold(self, user_id: str, base_threshold: int = 30) -> int:
        """
        Get personalized risk threshold for auto-approval.

        Args:
            user_id: User ID
            base_threshold: Base threshold (default 30)

        Returns:
            Adjusted threshold based on user's risk tolerance
        """
        profile = self.get_or_create_profile(user_id)

        # Adjust threshold based on risk tolerance
        # risk_tolerance: 0.0 (conservative) -> lower threshold (20)
        # risk_tolerance: 0.5 (balanced) -> base threshold (30)
        # risk_tolerance: 1.0 (aggressive) -> higher threshold (40)

        adjustment = (profile.risk_tolerance - 0.5) * 20
        adjusted = int(base_threshold + adjustment)

        return max(10, min(adjusted, 50))  # Clamp between 10-50

    def should_auto_approve(
        self,
        user_id: str,
        action_type: str,
        risk_score: int,
        base_threshold: int = 30,
    ) -> tuple[bool, float, str]:
        """
        Determine if action should be auto-approved based on learned preferences.

        Args:
            user_id: User ID
            action_type: Type of action
            risk_score: Risk score from assessment
            base_threshold: Base threshold for auto-approval

        Returns:
            Tuple of (should_auto_approve, confidence, reasoning)
        """
        profile = self.get_or_create_profile(user_id)

        # Get personalized threshold
        threshold = self.get_adjusted_risk_threshold(user_id, base_threshold)

        # Check historical approval rate for this action type
        patterns = profile.approval_patterns.get(action_type)
        if patterns:
            approved = patterns["approved"]
            rejected = patterns["rejected"]
            total = approved + rejected

            if total >= 3:
                approval_rate = approved / total

                # High approval rate for this action type
                if approval_rate > 0.8:
                    threshold += 5  # More lenient
                    confidence_boost = 0.1
                    reason_suffix = f" (user approves {action_type} {approval_rate*100:.0f}% of the time)"
                # Low approval rate
                elif approval_rate < 0.3:
                    threshold -= 5  # More conservative
                    confidence_boost = -0.1
                    reason_suffix = f" (user rejects {action_type} {(1-approval_rate)*100:.0f}% of the time)"
                else:
                    confidence_boost = 0.0
                    reason_suffix = ""
            else:
                confidence_boost = 0.0
                reason_suffix = ""
        else:
            confidence_boost = 0.0
            reason_suffix = ""

        # Decision
        should_approve = risk_score < threshold
        base_confidence = 0.7

        # Adjust confidence based on data
        if profile.total_interactions >= 10:
            confidence = base_confidence + 0.15 + confidence_boost
        elif profile.total_interactions >= 5:
            confidence = base_confidence + 0.1 + confidence_boost
        else:
            confidence = base_confidence + confidence_boost

        confidence = max(0.3, min(confidence, 0.95))

        # Build reasoning
        if should_approve:
            reasoning = (
                f"Auto-approving: risk score {risk_score} < threshold {threshold} "
                f"(base: {base_threshold}, adjusted for user's "
                f"{profile.risk_tolerance:.1f} risk tolerance)"
                f"{reason_suffix}"
            )
        else:
            reasoning = (
                f"Requesting approval: risk score {risk_score} >= threshold {threshold} "
                f"(base: {base_threshold}, adjusted for user){reason_suffix}"
            )

        return should_approve, confidence, reasoning

    def get_preference_insights(self, user_id: str) -> Dict:
        """
        Get insights about user preferences for UI display.

        Returns:
            Dict with preference insights
        """
        profile = self.get_or_create_profile(user_id)

        insights = {
            "risk_tolerance": profile.risk_tolerance,
            "total_interactions": profile.total_interactions,
            "preferences": {},
            "approval_rates": {},
        }

        # Add learned preferences
        for pref_type, pref in profile.preferences.items():
            if pref.confidence > 0.6:
                insights["preferences"][pref_type] = {
                    "value": pref.value,
                    "confidence": pref.confidence,
                }

        # Add approval rates by action type
        for action_type, patterns in profile.approval_patterns.items():
            total = patterns["approved"] + patterns["rejected"]
            if total > 0:
                insights["approval_rates"][action_type] = {
                    "rate": patterns["approved"] / total,
                    "total": total,
                }

        return insights

    def get_statistics(self) -> Dict:
        """Get global statistics for monitoring."""
        total_auto = self.global_stats["auto_approved_success"] + self.global_stats["auto_approved_complaints"]

        auto_success_rate = 0.0
        if total_auto > 0:
            auto_success_rate = self.global_stats["auto_approved_success"] / total_auto

        return {
            "total_approvals": self.global_stats["total_approvals"],
            "total_rejections": self.global_stats["total_rejections"],
            "auto_approved_success": self.global_stats["auto_approved_success"],
            "auto_approved_complaints": self.global_stats["auto_approved_complaints"],
            "auto_success_rate": auto_success_rate,
            "total_users": len(self._profiles_cache),
        }


# Global instance
_preference_engine = None


def get_preference_engine(db: Optional[Session] = None) -> PreferenceEngine:
    """Get global preference engine instance."""
    global _preference_engine
    if _preference_engine is None:
        _preference_engine = PreferenceEngine(db=db)
    elif db is not None:
        _preference_engine.set_db(db)
    return _preference_engine
