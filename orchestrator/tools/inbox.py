"""
Inbox/Email tools for the conversational agent.

Provides tools for searching and analyzing emails.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EmailItem(BaseModel):
    """An email item."""

    id: str = Field(description="Email ID")
    subject: str = Field(description="Email subject")
    sender: str = Field(description="Sender email/name")
    preview: str = Field(description="Body preview")
    received: str = Field(description="Received datetime")
    importance: str = Field(description="Importance level", default="medium")
    category: str = Field(description="Email category", default="other")


class EmailSearchOutput(BaseModel):
    """Output schema for email search."""

    emails: List[EmailItem] = Field(description="List of matching emails", default_factory=list)
    total_found: int = Field(description="Total number of matching emails")
    query: str = Field(description="Search query used")
    summary: str = Field(description="Summary of results")


class EmailSummaryOutput(BaseModel):
    """Output schema for email summary."""

    total_emails: int = Field(description="Total emails in inbox")
    unread_count: int = Field(description="Number of unread emails")
    important_count: int = Field(description="Number of important emails")
    categories: Dict[str, int] = Field(description="Count by category", default_factory=dict)
    top_senders: List[Dict[str, Any]] = Field(description="Top senders by email count", default_factory=list)
    summary: str = Field(description="Overall inbox summary")


def _get_db_session():
    """Get a database session."""
    from backend.api.database import SessionLocal

    return SessionLocal()


def _get_emails_from_db(
    search_query: Optional[str] = None,
    sender_filter: Optional[str] = None,
    importance_filter: Optional[str] = None,
    days_back: int = 7,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Fetch emails from database with optional filters."""
    try:
        from backend.api.models import Item, ItemAgentMetadata
        from sqlalchemy import or_

        db = _get_db_session()
        try:
            query = db.query(Item).filter(Item.source_type == "email")

            # Date filter
            cutoff = datetime.now() - timedelta(days=days_back)
            query = query.filter(Item.created_at >= cutoff)

            # Text search
            if search_query:
                search_pattern = f"%{search_query}%"
                query = query.filter(
                    or_(
                        Item.title.ilike(search_pattern),
                        Item.body_preview.ilike(search_pattern),
                        Item.sender.ilike(search_pattern),
                    )
                )

            # Sender filter
            if sender_filter:
                query = query.filter(Item.sender.ilike(f"%{sender_filter}%"))

            # Order by date
            query = query.order_by(Item.created_at.desc())

            emails = query.limit(limit).all()

            result = []
            for email in emails:
                metadata = email.agent_metadata
                importance = "medium"
                category = "other"
                if metadata:
                    importance = getattr(metadata, "importance", "medium") or "medium"
                    category = getattr(metadata, "category", "other") or "other"

                # Apply importance filter if specified
                if importance_filter and importance != importance_filter:
                    continue

                result.append(
                    {
                        "id": str(email.id),
                        "subject": email.title or "(No subject)",
                        "sender": email.sender or "Unknown",
                        "preview": (email.body_preview or "")[:200],
                        "received": email.created_at.isoformat() if email.created_at else "",
                        "importance": importance,
                        "category": category,
                    }
                )

            return result

        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to fetch emails: {e}")
        return []


@tool
def search_emails(query: str, days_back: int = 30, limit: int = 10) -> EmailSearchOutput:
    """
    Search emails by keyword in subject, body, or sender.

    Args:
        query: Search query (searches in subject, body, and sender)
        days_back: How many days back to search (default: 30)
        limit: Maximum number of results (default: 10)

    Returns:
        List of matching emails with relevance details
    """
    emails_data = _get_emails_from_db(search_query=query, days_back=days_back, limit=limit)

    emails = [
        EmailItem(
            id=e["id"],
            subject=e["subject"],
            sender=e["sender"],
            preview=e["preview"],
            received=e["received"],
            importance=e["importance"],
            category=e["category"],
        )
        for e in emails_data
    ]

    if not emails:
        summary = f"No emails found matching '{query}' in the last {days_back} days."
    elif len(emails) == 1:
        summary = f"Found 1 email matching '{query}': {emails[0].subject}"
    else:
        summary = f"Found {len(emails)} emails matching '{query}'."
        # Add context about top result
        summary += f" Most recent: '{emails[0].subject}' from {emails[0].sender}"

    return EmailSearchOutput(emails=emails, total_found=len(emails), query=query, summary=summary)


@tool
def get_recent_emails(
    limit: int = 10, importance: Optional[str] = None, sender: Optional[str] = None
) -> EmailSearchOutput:
    """
    Get recent emails with optional filters.

    Args:
        limit: Maximum number of emails (default: 10)
        importance: Filter by importance (critical, high, medium, low)
        sender: Filter by sender name or email

    Returns:
        List of recent emails
    """
    emails_data = _get_emails_from_db(sender_filter=sender, importance_filter=importance, days_back=14, limit=limit)

    emails = [
        EmailItem(
            id=e["id"],
            subject=e["subject"],
            sender=e["sender"],
            preview=e["preview"],
            received=e["received"],
            importance=e["importance"],
            category=e["category"],
        )
        for e in emails_data
    ]

    query_desc = "recent emails"
    if importance:
        query_desc = f"{importance} priority emails"
    if sender:
        query_desc = f"emails from {sender}"

    if not emails:
        summary = f"No {query_desc} found."
    else:
        # Group by importance
        important_count = len([e for e in emails if e.importance in ["critical", "high"]])
        summary = f"Found {len(emails)} {query_desc}."
        if important_count > 0:
            summary += f" {important_count} are marked as high priority."

    return EmailSearchOutput(emails=emails, total_found=len(emails), query=query_desc, summary=summary)


@tool
def get_email_summary() -> EmailSummaryOutput:
    """
    Get a summary of the inbox status.

    Provides overview of email counts, categories, and top senders.

    Returns:
        Inbox summary with statistics
    """
    try:
        from backend.api.models import Item
        from sqlalchemy import func

        db = _get_db_session()
        try:
            # Get total emails
            total = db.query(Item).filter(Item.source_type == "email").count()

            # Get emails from last 7 days
            week_ago = datetime.now() - timedelta(days=7)
            recent_query = db.query(Item).filter(Item.source_type == "email", Item.created_at >= week_ago)
            recent_count = recent_query.count()

            # Get category breakdown (from agent metadata)
            emails = recent_query.all()

            categories: Dict[str, int] = {}
            important_count = 0
            sender_counts: Dict[str, int] = {}

            for email in emails:
                # Count by sender
                sender = email.sender or "Unknown"
                sender_counts[sender] = sender_counts.get(sender, 0) + 1

                # Count by category and importance
                metadata = email.agent_metadata
                if metadata:
                    cat = getattr(metadata, "category", "other") or "other"
                    categories[cat] = categories.get(cat, 0) + 1

                    imp = getattr(metadata, "importance", "medium")
                    if imp in ["critical", "high"]:
                        important_count += 1

            # Get top senders
            top_senders = sorted(
                [{"sender": s, "count": c} for s, c in sender_counts.items()], key=lambda x: x["count"], reverse=True
            )[:5]

            # Build summary
            summary = f"Your inbox has {total} total emails. "
            summary += f"{recent_count} received in the last 7 days"
            if important_count > 0:
                summary += f", {important_count} marked as important"
            summary += "."

            if top_senders:
                summary += f" Top sender: {top_senders[0]['sender']} ({top_senders[0]['count']} emails)."

            return EmailSummaryOutput(
                total_emails=total,
                unread_count=recent_count,  # Using recent as proxy for unread
                important_count=important_count,
                categories=categories,
                top_senders=top_senders,
                summary=summary,
            )

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to get email summary: {e}")
        return EmailSummaryOutput(
            total_emails=0,
            unread_count=0,
            important_count=0,
            categories={},
            top_senders=[],
            summary="Unable to retrieve inbox summary.",
        )
