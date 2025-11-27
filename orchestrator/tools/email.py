"""
Email action tools for the conversational agent.

Provides a tool to draft emails as ActionProposals that require approval
before anything is sent.
"""

import logging
from typing import Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CreateEmailDraftOutput(BaseModel):
    """Output schema for creating an email draft."""

    success: bool = Field(description="Whether the draft proposal was created")
    draft_id: Optional[str] = Field(default=None, description="Draft identifier if already created")
    message: str = Field(description="Human-friendly status message")
    requires_approval: bool = Field(default=True, description="Whether this action needs approval")
    proposal_id: Optional[str] = Field(default=None, description="ID of the ActionProposal if created")


def _get_db_session():
    """Get a database session."""
    from backend.api.database import SessionLocal

    return SessionLocal()


@tool
def create_email_draft(to: str, subject: str, body: str, provider: str = "gmail") -> CreateEmailDraftOutput:
    """
    Prepare an email draft that will only be sent after user approval.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body content
        provider: Email provider (gmail|outlook). Defaults to gmail.

    Returns:
        Status of the draft creation request and proposal ID for approval
    """
    import uuid

    try:
        from backend.api.models import ActionProposal, User

        db = _get_db_session()
        try:
            user = db.query(User).first()
            if not user:
                return CreateEmailDraftOutput(
                    success=False,
                    message="No user account found to attach the draft.",
                    requires_approval=False,
                )

            proposal = ActionProposal(
                id=uuid.uuid4(),
                user_id=user.id,
                agent_name="conversational_agent",
                action_type="create_email_draft",
                payload={
                    "to": to,
                    "subject": subject,
                    "body": body,
                    "provider": provider,
                },
                status="pending",
                risk_level="low",
                explanation=f"Draft email to {to}: {subject or '(no subject)'}",
            )
            db.add(proposal)
            db.commit()

            return CreateEmailDraftOutput(
                success=True,
                message="Draft created and waiting for your approval.",
                requires_approval=True,
                proposal_id=str(proposal.id),
            )

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to create email draft proposal: {e}", exc_info=True)
        return CreateEmailDraftOutput(
            success=False,
            message=f"Failed to create draft: {str(e)}",
            requires_approval=False,
        )
