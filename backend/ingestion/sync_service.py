"""
Data ingestion and synchronization service.
"""

from datetime import datetime
from typing import Dict

from sqlalchemy.orm import Session

from backend.api.models import ConnectedAccount, Item
from backend.integrations.calendar import CalendarClient
from backend.integrations.gmail import GmailClient
from backend.integrations.outlook import OutlookClient


class SyncService:
    """Service for syncing data from external providers."""

    def __init__(self, db: Session):
        self.db = db

    def sync_gmail(self, account: ConnectedAccount) -> int:
        """Sync emails from Gmail account."""
        client = GmailClient.from_tokens(
            access_token=account.access_token,
            refresh_token=account.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=account.raw_metadata.get("client_id"),
            client_secret=account.raw_metadata.get("client_secret"),
        )

        messages = client.fetch_messages(max_results=50)
        count = 0

        for msg in messages:
            existing = (
                self.db.query(Item)
                .filter(
                    Item.user_id == account.user_id,
                    Item.source_id == msg["source_id"],
                    Item.source_provider == "gmail",
                )
                .first()
            )

            if not existing:
                item = Item(
                    user_id=account.user_id,
                    source_type="email",
                    source_provider="gmail",
                    source_account_id=account.id,
                    source_id=msg["source_id"],
                    title=msg["title"],
                    body_preview=msg["body_preview"],
                    body_full=msg["body_full"],
                    sender=msg["sender"],
                    recipients=msg["recipients"],
                    received_datetime=msg["received_datetime"],
                    raw_metadata=msg["raw_metadata"],
                )
                self.db.add(item)
                count += 1

        self.db.commit()
        account.last_sync_at = datetime.utcnow()
        self.db.commit()

        return count

    def sync_outlook(self, account: ConnectedAccount) -> int:
        """Sync emails from Outlook account."""
        client = OutlookClient.from_refresh_token(
            client_id=account.raw_metadata.get("client_id"),
            client_secret=account.raw_metadata.get("client_secret"),
            refresh_token=account.refresh_token,
        )

        messages = client.fetch_messages(max_results=50)
        count = 0

        for msg in messages:
            existing = (
                self.db.query(Item)
                .filter(
                    Item.user_id == account.user_id,
                    Item.source_id == msg["source_id"],
                    Item.source_provider == "outlook",
                )
                .first()
            )

            if not existing:
                item = Item(
                    user_id=account.user_id,
                    source_type="email",
                    source_provider="outlook",
                    source_account_id=account.id,
                    source_id=msg["source_id"],
                    title=msg["title"],
                    body_preview=msg["body_preview"],
                    body_full=msg["body_full"],
                    sender=msg["sender"],
                    recipients=msg["recipients"],
                    received_datetime=msg["received_datetime"],
                    raw_metadata=msg["raw_metadata"],
                )
                self.db.add(item)
                count += 1

        self.db.commit()
        account.last_sync_at = datetime.utcnow()
        self.db.commit()

        return count

    def sync_calendar(self, account: ConnectedAccount) -> int:
        """Sync events from Google Calendar."""
        client = CalendarClient.from_tokens(
            access_token=account.access_token,
            refresh_token=account.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=account.raw_metadata.get("client_id"),
            client_secret=account.raw_metadata.get("client_secret"),
        )

        events = client.fetch_events(days_ahead=14)
        count = 0

        for event in events:
            existing = (
                self.db.query(Item)
                .filter(
                    Item.user_id == account.user_id,
                    Item.source_id == event["source_id"],
                    Item.source_provider == "google_calendar",
                )
                .first()
            )

            if not existing:
                item = Item(
                    user_id=account.user_id,
                    source_type="event",
                    source_provider="google_calendar",
                    source_account_id=account.id,
                    source_id=event["source_id"],
                    title=event["title"],
                    body_preview=event["body_preview"],
                    body_full=event["body_full"],
                    sender=event["sender"],
                    recipients=event["recipients"],
                    start_datetime=event["start_datetime"],
                    end_datetime=event["end_datetime"],
                    received_datetime=event["received_datetime"],
                    raw_metadata=event["raw_metadata"],
                )
                self.db.add(item)
                count += 1
            else:
                # Update existing event
                existing.title = event["title"]
                existing.start_datetime = event["start_datetime"]
                existing.end_datetime = event["end_datetime"]

        self.db.commit()
        account.last_sync_at = datetime.utcnow()
        self.db.commit()

        return count

    def sync_all_accounts(self, user_id: str) -> Dict[str, int]:
        """Sync all connected accounts for a user."""
        accounts = (
            self.db.query(ConnectedAccount)
            .filter(ConnectedAccount.user_id == user_id, ConnectedAccount.status == "active")
            .all()
        )

        results = {}
        for account in accounts:
            try:
                if account.provider == "gmail":
                    results["gmail"] = self.sync_gmail(account)
                elif account.provider == "outlook":
                    results["outlook"] = self.sync_outlook(account)
                elif account.provider == "google_calendar":
                    results["google_calendar"] = self.sync_calendar(account)
            except Exception as e:
                results[account.provider] = f"Error: {str(e)}"

        return results
