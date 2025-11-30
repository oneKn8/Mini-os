"""
Data ingestion and synchronization service.

Enhanced with RAG indexing for semantic search capabilities.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from datetime import timedelta

from sqlalchemy.orm import Session

from backend.api.models import ConnectedAccount, Item
from backend.integrations.calendar import CalendarClient
from backend.integrations.gmail import GmailClient
from backend.integrations.outlook import OutlookClient

logger = logging.getLogger(__name__)


class RAGIndexer:
    """
    Indexes items into the vectorstore for semantic search.

    This enables the RAG agent to search through emails, events,
    and other user data using natural language queries.
    """

    def __init__(self):
        self._vectorstore = None
        self._embedder = None
        self._initialized = False

    def _init_vectorstore(self):
        """Lazily initialize the vectorstore."""
        if self._initialized:
            return self._vectorstore is not None

        self._initialized = True

        try:
            from backend.rag import (
                get_embedding_model,
                create_vectorstore_langchain,
                is_rag_available,
            )

            if not is_rag_available():
                logger.warning("RAG not available - indexing disabled")
                return False

            self._embedder = get_embedding_model()
            self._vectorstore = create_vectorstore_langchain(self._embedder)
            logger.info("RAG indexer initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize RAG indexer: {e}")
            return False

    def index_item(self, item: Item) -> bool:
        """
        Index a single item into the vectorstore.

        Args:
            item: The Item to index

        Returns:
            True if indexed successfully
        """
        if not self._init_vectorstore():
            return False

        try:
            from langchain_core.documents import Document

            # Build document content
            content_parts = []

            if item.title:
                content_parts.append(f"Subject: {item.title}")
            if item.sender:
                content_parts.append(f"From: {item.sender}")
            if item.body_preview:
                content_parts.append(item.body_preview)
            if item.body_full and len(item.body_full) > len(item.body_preview or ""):
                # Add full body if it has more content
                content_parts.append(item.body_full[:2000])  # Limit size

            content = "\n".join(content_parts)

            if not content.strip():
                return False

            # Build metadata
            metadata = {
                "source": f"{item.source_type}:{item.id}",
                "source_type": item.source_type,
                "source_provider": item.source_provider,
                "item_id": str(item.id),
                "user_id": str(item.user_id),
                "title": item.title or "",
                "sender": item.sender or "",
            }

            if item.received_datetime:
                metadata["received_date"] = item.received_datetime.isoformat()
            if item.start_datetime:
                metadata["start_date"] = item.start_datetime.isoformat()

            # Create document
            doc = Document(page_content=content, metadata=metadata)

            # Add to vectorstore
            self._vectorstore.add_documents([doc])
            logger.debug(f"Indexed item {item.id}: {item.title[:50] if item.title else 'Untitled'}")
            return True

        except Exception as e:
            logger.error(f"Failed to index item {item.id}: {e}")
            return False

    def index_items(self, items: List[Item]) -> int:
        """
        Index multiple items into the vectorstore.

        Args:
            items: List of Items to index

        Returns:
            Number of items successfully indexed
        """
        if not self._init_vectorstore():
            return 0

        indexed = 0
        for item in items:
            if self.index_item(item):
                indexed += 1

        logger.info(f"Indexed {indexed}/{len(items)} items")
        return indexed

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search the vectorstore.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching documents with metadata
        """
        if not self._init_vectorstore():
            return []

        try:
            docs = self._vectorstore.similarity_search(query, k=limit)
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                }
                for doc in docs
            ]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []


# Global indexer instance
_indexer: Optional[RAGIndexer] = None


def get_indexer() -> RAGIndexer:
    """Get or create the global RAG indexer."""
    global _indexer
    if _indexer is None:
        _indexer = RAGIndexer()
    return _indexer


class SyncService:
    """Service for syncing data from external providers."""

    def __init__(self, db: Session, enable_indexing: bool = True):
        self.db = db
        self.enable_indexing = enable_indexing
        self._indexer = get_indexer() if enable_indexing else None

    def _index_items(self, items: List[Item]) -> int:
        """Index items if indexing is enabled."""
        if self._indexer and items:
            return self._indexer.index_items(items)
        return 0

    def sync_gmail(self, account: ConnectedAccount) -> int:
        """Sync emails from Gmail account."""
        # Get client credentials from scopes JSONB or env vars
        if account.scopes and isinstance(account.scopes, dict):
            client_id = account.scopes.get("client_id")
            client_secret = account.scopes.get("client_secret")
        else:
            # Fallback to reading from env/file
            import os
            import json

            gmail_secret_path = os.getenv("GMAIL_CLIENT_SECRET_PATH")
            if gmail_secret_path and os.path.exists(gmail_secret_path):
                with open(gmail_secret_path) as f:
                    creds_data = json.load(f)
                    client_id = creds_data["installed"]["client_id"]
                    client_secret = creds_data["installed"]["client_secret"]
            else:
                raise ValueError("Gmail client credentials not found")

        client = GmailClient.from_tokens(
            access_token=account.access_token,
            refresh_token=account.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
        )

        target_count = 500
        synced = 0
        new_items = []
        page_token = None
        query = "newer_than:365d"

        while synced < target_count:
            batch = client.fetch_messages(max_results=100, query=query, page_token=page_token)
            messages = batch.get("messages", [])
            page_token = batch.get("next_page_token")

            if not messages:
                break

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
                        thread_id=msg.get("thread_id"),
                        title=msg["title"],
                        body_preview=msg["body_preview"],
                        body_full=msg["body_full"],
                        sender=msg["sender"],
                        recipients=msg["recipients"],
                        received_datetime=msg["received_datetime"],
                        raw_metadata=msg["raw_metadata"],
                    )
                    self.db.add(item)
                    new_items.append(item)
                    synced += 1

                if synced >= target_count:
                    break

            if not page_token:
                break

        self.db.commit()

        # Refresh items to get IDs
        for item in new_items:
            self.db.refresh(item)

        # Index new items for RAG
        if new_items:
            indexed = self._index_items(new_items)
            logger.info(f"Gmail sync: {synced} new emails, {indexed} indexed for search")

        account.last_sync_at = datetime.utcnow()
        self.db.commit()

        return synced

    def resync_gmail_items(self, account: ConnectedAccount, limit: int = 100, newer_than_days: Optional[int] = 365) -> int:
        """
        Re-fetch and update existing Gmail items to backfill HTML bodies and metadata.
        """
        # Get client credentials from scopes JSONB or env vars
        if account.scopes and isinstance(account.scopes, dict):
            client_id = account.scopes.get("client_id")
            client_secret = account.scopes.get("client_secret")
        else:
            import os
            import json

            gmail_secret_path = os.getenv("GMAIL_CLIENT_SECRET_PATH")
            if gmail_secret_path and os.path.exists(gmail_secret_path):
                with open(gmail_secret_path) as f:
                    creds_data = json.load(f)
                    client_id = creds_data["installed"]["client_id"]
                    client_secret = creds_data["installed"]["client_secret"]
            else:
                raise ValueError("Gmail client credentials not found")

        client = GmailClient.from_tokens(
            access_token=account.access_token,
            refresh_token=account.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
        )

        query = self.db.query(Item).filter(
            Item.user_id == account.user_id,
            Item.source_provider == "gmail",
            Item.source_account_id == account.id,
        )

        if newer_than_days:
            cutoff = datetime.utcnow() - timedelta(days=newer_than_days)
            query = query.filter(Item.received_datetime != None, Item.received_datetime > cutoff)

        items = query.order_by(Item.received_datetime.desc()).limit(limit).all()

        updated = 0
        for item in items:
            try:
                msg = client.fetch_message_by_id(item.source_id)
                item.body_full = msg["body_full"]
                item.body_preview = msg["body_preview"]
                item.raw_metadata = msg["raw_metadata"]
                item.title = msg["title"]
                item.sender = msg["sender"]
                item.recipients = msg["recipients"]
                item.received_datetime = msg["received_datetime"]
                item.thread_id = msg.get("thread_id")
                updated += 1
            except Exception as e:
                logger.error(f"Failed to resync message {item.source_id}: {e}")

        self.db.commit()
        if updated:
            logger.info(f"Resynced {updated} Gmail items for account {account.id}")
        return updated

    def sync_outlook(self, account: ConnectedAccount) -> int:
        """Sync emails from Outlook account."""
        client = OutlookClient.from_refresh_token(
            client_id=account.raw_metadata.get("client_id"),
            client_secret=account.raw_metadata.get("client_secret"),
            refresh_token=account.refresh_token,
        )

        messages = client.fetch_messages(max_results=50)
        count = 0
        new_items = []

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
                new_items.append(item)
                count += 1

        self.db.commit()

        # Refresh and index
        for item in new_items:
            self.db.refresh(item)

        if new_items:
            indexed = self._index_items(new_items)
            logger.info(f"Outlook sync: {count} new emails, {indexed} indexed for search")

        account.last_sync_at = datetime.utcnow()
        self.db.commit()

        return count

    def sync_calendar(self, account: ConnectedAccount) -> int:
        """Sync events from Google Calendar."""
        # Get client credentials from scopes JSONB or env vars
        if account.scopes and isinstance(account.scopes, dict):
            client_id = account.scopes.get("client_id")
            client_secret = account.scopes.get("client_secret")
        else:
            # Fallback to reading from env/file
            import os
            import json

            calendar_secret_path = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET_PATH")
            if calendar_secret_path and os.path.exists(calendar_secret_path):
                with open(calendar_secret_path) as f:
                    creds_data = json.load(f)
                    client_id = creds_data["installed"]["client_id"]
                    client_secret = creds_data["installed"]["client_secret"]
            else:
                raise ValueError("Calendar client credentials not found")

        client = CalendarClient.from_tokens(
            access_token=account.access_token,
            refresh_token=account.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
        )

        events = client.fetch_events(days_ahead=14)
        count = 0
        new_items = []

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
                new_items.append(item)
                count += 1
            else:
                # Update existing event
                existing.title = event["title"]
                existing.start_datetime = event["start_datetime"]
                existing.end_datetime = event["end_datetime"]

        self.db.commit()

        # Refresh and index
        for item in new_items:
            self.db.refresh(item)

        if new_items:
            indexed = self._index_items(new_items)
            logger.info(f"Calendar sync: {count} new events, {indexed} indexed for search")

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
                logger.error(f"Sync failed for {account.provider}: {e}")
                results[account.provider] = f"Error: {str(e)}"

        return results

    def reindex_all_items(self, user_id: Optional[str] = None) -> int:
        """
        Reindex all items in the vectorstore.

        Useful for rebuilding the search index after schema changes
        or if the vectorstore was cleared.

        Args:
            user_id: Optional user ID to filter by

        Returns:
            Number of items indexed
        """
        if not self._indexer:
            logger.warning("Indexing not enabled")
            return 0

        query = self.db.query(Item)
        if user_id:
            query = query.filter(Item.user_id == user_id)

        items = query.all()
        logger.info(f"Reindexing {len(items)} items...")

        indexed = self._indexer.index_items(items)
        logger.info(f"Reindex complete: {indexed}/{len(items)} items indexed")

        return indexed
