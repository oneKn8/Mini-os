"""
Action Executor - Executes approved action proposals.
"""

from datetime import datetime
from typing import Dict

from sqlalchemy.orm import Session

from backend.api.models import ActionProposal, ExecutionLog
from backend.integrations.calendar import CalendarClient
from backend.integrations.gmail import GmailClient
from backend.integrations.outlook import OutlookClient


class ActionExecutor:
    """Executes approved actions on external services."""

    def __init__(self, db: Session):
        self.db = db

    def execute(self, proposal: ActionProposal) -> ExecutionLog:
        """Execute an approved action proposal."""
        start_time = datetime.utcnow()

        try:
            result = None
            if proposal.action_type == "create_email_draft":
                result = self._create_email_draft(proposal)
            elif proposal.action_type == "create_calendar_event":
                result = self._create_calendar_event(proposal)
            elif proposal.action_type == "update_calendar_event":
                result = self._update_calendar_event(proposal)
            elif proposal.action_type == "delete_calendar_event":
                result = self._delete_calendar_event(proposal)
            else:
                raise ValueError(f"Unknown action type: {proposal.action_type}")

            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            log = ExecutionLog(
                user_id=proposal.user_id,
                action_proposal_id=proposal.id,
                executor_status="success",
                external_ids=result,
                request_payload=proposal.payload,
                execution_duration_ms=duration_ms,
            )

            proposal.status = "executed"
            proposal.executed_at = datetime.utcnow()

        except Exception as e:
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            log = ExecutionLog(
                user_id=proposal.user_id,
                action_proposal_id=proposal.id,
                executor_status="failure",
                executor_error=str(e),
                request_payload=proposal.payload,
                execution_duration_ms=duration_ms,
            )

            proposal.status = "failed"

        self.db.add(log)
        self.db.commit()

        return log

    def _create_email_draft(self, proposal: ActionProposal) -> Dict:
        """Create an email draft."""
        payload = proposal.payload
        provider = payload.get("provider", "gmail")

        if provider == "gmail":
            client = self._get_gmail_client(proposal.user_id)
            result = client.create_draft(to=payload["to"], subject=payload["subject"], body=payload["body"])
        elif provider == "outlook":
            client = self._get_outlook_client(proposal.user_id)
            result = client.create_draft(to=payload["to"], subject=payload["subject"], body=payload["body"])
        else:
            raise ValueError(f"Unknown provider: {provider}")

        return result

    def _create_calendar_event(self, proposal: ActionProposal) -> Dict:
        """Create a calendar event."""
        payload = proposal.payload
        client = self._get_calendar_client(proposal.user_id)

        from datetime import datetime

        start = datetime.fromisoformat(payload["start"])
        end = datetime.fromisoformat(payload["end"])

        result = client.create_event(
            title=payload["title"],
            start=start,
            end=end,
            description=payload.get("description", ""),
            location=payload.get("location", ""),
        )

        return result

    def _update_calendar_event(self, proposal: ActionProposal) -> Dict:
        """Update a calendar event."""
        payload = proposal.payload
        client = self._get_calendar_client(proposal.user_id)

        result = client.update_event(event_id=payload["event_id"], **payload.get("updates", {}))

        return result

    def _delete_calendar_event(self, proposal: ActionProposal) -> Dict:
        """Delete a calendar event."""
        payload = proposal.payload
        client = self._get_calendar_client(proposal.user_id)

        client.delete_event(event_id=payload["event_id"])

        return {"deleted": True, "event_id": payload["event_id"]}

    def _get_gmail_client(self, user_id: str) -> GmailClient:
        """Get Gmail client for user."""
        from backend.api.models import ConnectedAccount

        account = (
            self.db.query(ConnectedAccount)
            .filter(
                ConnectedAccount.user_id == user_id,
                ConnectedAccount.provider == "gmail",
                ConnectedAccount.status == "active",
            )
            .first()
        )

        if not account:
            raise ValueError("No active Gmail account")

        return GmailClient.from_tokens(
            access_token=account.access_token,
            refresh_token=account.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=account.raw_metadata.get("client_id"),
            client_secret=account.raw_metadata.get("client_secret"),
        )

    def _get_outlook_client(self, user_id: str) -> OutlookClient:
        """Get Outlook client for user."""
        from backend.api.models import ConnectedAccount

        account = (
            self.db.query(ConnectedAccount)
            .filter(
                ConnectedAccount.user_id == user_id,
                ConnectedAccount.provider == "outlook",
                ConnectedAccount.status == "active",
            )
            .first()
        )

        if not account:
            raise ValueError("No active Outlook account")

        return OutlookClient.from_refresh_token(
            client_id=account.raw_metadata.get("client_id"),
            client_secret=account.raw_metadata.get("client_secret"),
            refresh_token=account.refresh_token,
        )

    def _get_calendar_client(self, user_id: str) -> CalendarClient:
        """Get Calendar client for user."""
        from backend.api.models import ConnectedAccount

        account = (
            self.db.query(ConnectedAccount)
            .filter(
                ConnectedAccount.user_id == user_id,
                ConnectedAccount.provider == "google_calendar",
                ConnectedAccount.status == "active",
            )
            .first()
        )

        if not account:
            raise ValueError("No active Calendar account")

        return CalendarClient.from_tokens(
            access_token=account.access_token,
            refresh_token=account.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=account.raw_metadata.get("client_id"),
            client_secret=account.raw_metadata.get("client_secret"),
        )
