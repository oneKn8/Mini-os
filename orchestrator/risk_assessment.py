"""
Risk Assessment System for Action Proposals.

Intelligent risk scoring to reduce approval fatigue by auto-approving low-risk actions.
Target: 60% reduction in approval requests.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RiskScore:
    """Risk score breakdown for an action."""

    total_score: int  # 0-100
    reversibility_score: int  # 0-20
    impact_score: int  # 0-30
    sensitivity_score: int  # 0-25
    history_score: int  # 0-15
    time_score: int  # 0-10

    auto_approve: bool
    confidence: float  # 0.0-1.0
    reasoning: str

    def should_auto_approve(self) -> bool:
        """Determine if action should be auto-approved."""
        return self.auto_approve and self.total_score < 30


@dataclass
class ActionContext:
    """Context for risk assessment."""

    action_type: str
    payload: Dict
    user_id: str
    user_history: Optional[List[Dict]] = None
    similar_approvals: int = 0
    similar_rejections: int = 0


class RiskAssessor:
    """
    Intelligent risk assessment for action proposals.

    Scoring System (0-100):
    - 0-29: Low risk (auto-approve)
    - 30-69: Medium risk (request approval)
    - 70-100: High risk (always request approval)

    Components:
    1. Reversibility (0-20): Can the action be undone?
    2. Impact (0-30): How many people/items affected?
    3. Sensitivity (0-25): Does it involve private/sensitive data?
    4. History (0-15): User's past decisions on similar actions
    5. Time (0-10): Time sensitivity and urgency
    """

    # Risk profiles for common action types
    ACTION_RISK_PROFILES = {
        "create_email_draft": {
            "base_reversibility": 5,  # Drafts are easily deleted
            "base_sensitivity": 10,  # Emails can contain sensitive info
            "base_impact": 5,  # Only creates draft, doesn't send
        },
        "send_email": {
            "base_reversibility": 18,  # Can't unsend (unless recall works)
            "base_sensitivity": 15,  # Sent emails are more sensitive
            "base_impact": 20,  # Affects recipients
        },
        "create_calendar_event": {
            "base_reversibility": 5,  # Easy to delete/modify
            "base_sensitivity": 8,  # Calendar data is semi-sensitive
            "base_impact": 12,  # Affects attendees' calendars
        },
        "delete_email": {
            "base_reversibility": 15,  # Usually can recover from trash
            "base_sensitivity": 10,  # Depends on email content
            "base_impact": 5,  # Only affects user
        },
        "update_preferences": {
            "base_reversibility": 5,  # Easy to change back
            "base_sensitivity": 5,  # User preferences are low sensitivity
            "base_impact": 5,  # Only affects user
        },
        "search_emails": {
            "base_reversibility": 0,  # Read-only operation
            "base_sensitivity": 8,  # Reading sensitive data
            "base_impact": 0,  # No changes made
        },
        "query_knowledge_base": {
            "base_reversibility": 0,  # Read-only
            "base_sensitivity": 5,  # Depends on KB content
            "base_impact": 0,  # No changes
        },
    }

    def __init__(self):
        """Initialize risk assessor."""
        self.approval_history: Dict[str, List[Dict]] = {}  # user_id -> history

    def assess(self, context: ActionContext) -> RiskScore:
        """
        Assess risk for an action proposal.

        Args:
            context: Action context with user history

        Returns:
            RiskScore with detailed breakdown
        """
        action_type = context.action_type
        payload = context.payload

        # Get base risk profile
        profile = self.ACTION_RISK_PROFILES.get(
            action_type, {"base_reversibility": 10, "base_sensitivity": 10, "base_impact": 10}
        )

        # Calculate component scores
        reversibility_score = self._calculate_reversibility(action_type, payload, profile)
        impact_score = self._calculate_impact(action_type, payload, profile)
        sensitivity_score = self._calculate_sensitivity(action_type, payload, profile)
        history_score = self._calculate_history(context)
        time_score = self._calculate_time_sensitivity(action_type, payload)

        # Total score
        total_score = reversibility_score + impact_score + sensitivity_score + history_score + time_score

        # Determine auto-approval
        auto_approve = total_score < 30
        confidence = self._calculate_confidence(context, total_score)

        # Build reasoning
        reasoning = self._build_reasoning(
            action_type, total_score, reversibility_score, impact_score, sensitivity_score, history_score, time_score
        )

        logger.info(
            f"Risk assessment for {action_type}: score={total_score}, "
            f"auto_approve={auto_approve}, confidence={confidence:.2f}"
        )

        return RiskScore(
            total_score=total_score,
            reversibility_score=reversibility_score,
            impact_score=impact_score,
            sensitivity_score=sensitivity_score,
            history_score=history_score,
            time_score=time_score,
            auto_approve=auto_approve,
            confidence=confidence,
            reasoning=reasoning,
        )

    def _calculate_reversibility(self, action_type: str, payload: Dict, profile: Dict) -> int:
        """
        Calculate reversibility score (0-20).

        Lower score = more reversible (safer)
        Higher score = irreversible (riskier)
        """
        base_score = profile.get("base_reversibility", 10)

        # Read-only operations are fully reversible
        if action_type in ["search_emails", "query_knowledge_base", "get_upcoming_events"]:
            return 0

        # Draft operations are easily reversible
        if "draft" in action_type or "create" in action_type:
            return min(base_score, 8)

        # Send/delete operations are less reversible
        if "send" in action_type or "delete" in action_type:
            return max(base_score, 12)

        return base_score

    def _calculate_impact(self, action_type: str, payload: Dict, profile: Dict) -> int:
        """
        Calculate impact score (0-30).

        Based on number of people/items affected.
        """
        base_score = profile.get("base_impact", 10)

        # Check for recipients/attendees
        recipients = []
        if "to" in payload:
            recipients = payload["to"] if isinstance(payload["to"], list) else [payload["to"]]
        elif "attendees" in payload:
            attendees = payload["attendees"]
            recipients = attendees if isinstance(attendees, list) else [attendees]

        # Scale impact by number of recipients
        if recipients:
            num_recipients = len(recipients)
            if num_recipients == 1:
                return base_score
            elif num_recipients <= 5:
                return base_score + 5
            elif num_recipients <= 20:
                return base_score + 10
            else:
                return min(base_score + 15, 30)

        # No external impact
        return base_score

    def _calculate_sensitivity(self, action_type: str, payload: Dict, profile: Dict) -> int:
        """
        Calculate sensitivity score (0-25).

        Based on data privacy and confidentiality.
        """
        base_score = profile.get("base_sensitivity", 10)

        # Check for sensitive keywords in content
        sensitive_keywords = [
            "password",
            "confidential",
            "secret",
            "private",
            "salary",
            "credit card",
            "ssn",
            "financial",
            "legal",
            "contract",
            "termination",
            "layoff",
        ]

        content = str(payload.get("body", "")) + str(payload.get("subject", ""))
        content_lower = content.lower()

        sensitive_count = sum(1 for keyword in sensitive_keywords if keyword in content_lower)

        if sensitive_count >= 3:
            return min(base_score + 10, 25)
        elif sensitive_count >= 1:
            return min(base_score + 5, 25)

        # Check for external domains (higher risk)
        if "to" in payload:
            recipients = payload["to"] if isinstance(payload["to"], list) else [payload["to"]]
            external_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]
            has_external = any(any(domain in str(r).lower() for domain in external_domains) for r in recipients)
            if has_external:
                return min(base_score + 3, 25)

        return base_score

    def _calculate_history(self, context: ActionContext) -> int:
        """
        Calculate history score (0-15).

        Based on user's past approval patterns.
        Lower score = user consistently approves (safer to auto-approve)
        Higher score = inconsistent or no history (riskier)
        """
        similar_approvals = context.similar_approvals
        similar_rejections = context.similar_rejections

        total_similar = similar_approvals + similar_rejections

        # No history - moderate risk
        if total_similar == 0:
            return 10

        # Calculate approval rate
        approval_rate = similar_approvals / total_similar

        # High approval rate (>80%) - low risk
        if approval_rate > 0.8 and total_similar >= 3:
            return 0

        # Moderate approval rate (50-80%) - moderate risk
        if approval_rate > 0.5:
            return 5

        # Low approval rate (<50%) - high risk
        return 12

    def _calculate_time_sensitivity(self, action_type: str, payload: Dict) -> int:
        """
        Calculate time sensitivity score (0-10).

        Urgent actions get lower scores (safer to auto-approve).
        """
        # Check for urgency keywords
        urgent_keywords = ["urgent", "asap", "immediately", "emergency", "critical"]

        subject = payload.get("subject", "").lower()
        body = payload.get("body", "").lower()
        title = payload.get("title", "").lower()

        content = f"{subject} {body} {title}"

        is_urgent = any(keyword in content for keyword in urgent_keywords)

        if is_urgent:
            return 3  # Urgent actions are time-sensitive, lower risk to delay

        # Check for scheduled events in near future
        if "start_time" in payload:
            try:
                start_time = datetime.fromisoformat(payload["start_time"].replace("Z", "+00:00"))
                time_until = (start_time - datetime.now(start_time.tzinfo)).total_seconds()

                # Event in next hour - urgent
                if time_until < 3600:
                    return 2
                # Event in next 24 hours
                elif time_until < 86400:
                    return 4
            except Exception:
                pass

        return 5  # Default: moderate time sensitivity

    def _calculate_confidence(self, context: ActionContext, total_score: int) -> float:
        """Calculate confidence in the risk assessment (0.0-1.0)."""
        confidence = 0.7  # Base confidence

        # Increase confidence with more history
        total_similar = context.similar_approvals + context.similar_rejections
        if total_similar >= 5:
            confidence += 0.15
        elif total_similar >= 2:
            confidence += 0.1

        # Known action types increase confidence
        if context.action_type in self.ACTION_RISK_PROFILES:
            confidence += 0.1

        # Very low or very high scores are more confident
        if total_score < 20 or total_score > 70:
            confidence += 0.05

        return min(confidence, 1.0)

    def _build_reasoning(
        self, action_type: str, total: int, rev: int, impact: int, sens: int, hist: int, time: int
    ) -> str:
        """Build human-readable reasoning for the risk score."""
        if total < 30:
            risk_level = "Low risk"
            recommendation = "Safe to auto-approve"
        elif total < 70:
            risk_level = "Medium risk"
            recommendation = "Requesting user approval"
        else:
            risk_level = "High risk"
            recommendation = "Requires careful review"

        components = []
        if rev > 10:
            components.append(f"difficult to reverse (score: {rev})")
        if impact > 15:
            components.append(f"significant impact (score: {impact})")
        if sens > 15:
            components.append(f"sensitive data (score: {sens})")
        if hist > 10:
            components.append(f"limited history (score: {hist})")

        if components:
            detail = " - " + ", ".join(components)
        else:
            detail = ""

        return f"{risk_level} (total: {total}/100). {recommendation}.{detail}"

    def record_decision(self, user_id: str, action_type: str, approved: bool, payload: Dict):
        """
        Record user decision for future learning.

        Args:
            user_id: User ID
            action_type: Action type
            approved: Whether user approved
            payload: Action payload
        """
        if user_id not in self.approval_history:
            self.approval_history[user_id] = []

        self.approval_history[user_id].append(
            {
                "action_type": action_type,
                "approved": approved,
                "payload": payload,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Keep only last 100 decisions per user
        if len(self.approval_history[user_id]) > 100:
            self.approval_history[user_id] = self.approval_history[user_id][-100:]

        logger.info(f"Recorded decision for {user_id}: {action_type} -> {approved}")

    def get_user_history(self, user_id: str, action_type: str) -> Dict[str, int]:
        """
        Get user's approval history for similar actions.

        Returns:
            Dict with 'approvals' and 'rejections' counts
        """
        if user_id not in self.approval_history:
            return {"approvals": 0, "rejections": 0}

        history = self.approval_history[user_id]
        similar_actions = [h for h in history if h["action_type"] == action_type]

        approvals = sum(1 for h in similar_actions if h["approved"])
        rejections = len(similar_actions) - approvals

        return {"approvals": approvals, "rejections": rejections}


# Global instance
_risk_assessor = None


def get_risk_assessor() -> RiskAssessor:
    """Get global risk assessor instance."""
    global _risk_assessor
    if _risk_assessor is None:
        _risk_assessor = RiskAssessor()
    return _risk_assessor
