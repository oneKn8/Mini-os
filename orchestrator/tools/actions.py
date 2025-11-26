"""
Actions tools for the conversational agent.

Provides tools for managing pending actions and approvals.
"""

import logging
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PendingAction(BaseModel):
    """A pending action awaiting approval."""

    id: str = Field(description="Action ID")
    action_type: str = Field(description="Type of action")
    agent_name: str = Field(description="Agent that proposed this action")
    explanation: str = Field(description="What this action will do")
    risk_level: str = Field(description="Risk level: low, medium, high")
    created_at: str = Field(description="When this action was proposed")
    payload_summary: str = Field(description="Summary of action payload")


class PendingActionsOutput(BaseModel):
    """Output schema for pending actions."""

    actions: List[PendingAction] = Field(description="List of pending actions", default_factory=list)
    total_count: int = Field(description="Total number of pending actions")
    high_risk_count: int = Field(description="Number of high risk actions")
    summary: str = Field(description="Summary of pending actions")


def _get_db_session():
    """Get a database session."""
    from backend.api.database import SessionLocal

    return SessionLocal()


def _summarize_payload(action_type: str, payload: Dict[str, Any]) -> str:
    """Create a human-readable summary of an action payload."""
    if action_type == "create_calendar_event":
        title = payload.get("title", "Untitled")
        start = payload.get("start", "")
        return f"Create event '{title}' at {start}"
    elif action_type == "create_email_draft":
        to = payload.get("to", "")
        subject = payload.get("subject", "")
        return f"Draft email to {to}: {subject}"
    elif action_type == "send_email":
        to = payload.get("to", "")
        return f"Send email to {to}"
    else:
        return f"{action_type}: {str(payload)[:100]}"


@tool
def get_pending_actions(risk_level: Optional[str] = None, limit: int = 10) -> PendingActionsOutput:
    """
    Get actions pending user approval.

    Shows all actions proposed by agents that need user review before execution.

    Args:
        risk_level: Filter by risk level (low, medium, high)
        limit: Maximum number of actions to return (default: 10)

    Returns:
        List of pending actions awaiting approval
    """
    try:
        from backend.api.models import ActionProposal

        db = _get_db_session()
        try:
            query = (
                db.query(ActionProposal)
                .filter(ActionProposal.status == "pending")
                .order_by(ActionProposal.created_at.desc())
            )

            if risk_level:
                query = query.filter(ActionProposal.risk_level == risk_level)

            proposals = query.limit(limit).all()

            actions = []
            high_risk_count = 0

            for p in proposals:
                payload_summary = _summarize_payload(p.action_type, p.payload or {})

                actions.append(
                    PendingAction(
                        id=str(p.id),
                        action_type=p.action_type,
                        agent_name=p.agent_name,
                        explanation=p.explanation or payload_summary,
                        risk_level=p.risk_level or "low",
                        created_at=p.created_at.isoformat() if p.created_at else "",
                        payload_summary=payload_summary,
                    )
                )

                if p.risk_level == "high":
                    high_risk_count += 1

            # Build summary
            if not actions:
                summary = "You have no pending actions. All caught up!"
            elif len(actions) == 1:
                summary = f"You have 1 pending action: {actions[0].explanation}"
            else:
                summary = f"You have {len(actions)} pending actions."
                if high_risk_count > 0:
                    summary += f" {high_risk_count} are marked as high risk and need careful review."

            return PendingActionsOutput(
                actions=actions, total_count=len(actions), high_risk_count=high_risk_count, summary=summary
            )

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to get pending actions: {e}")
        return PendingActionsOutput(
            actions=[], total_count=0, high_risk_count=0, summary=f"Unable to retrieve pending actions: {str(e)}"
        )
