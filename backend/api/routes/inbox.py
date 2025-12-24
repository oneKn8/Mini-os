"""
Inbox API routes
"""

from typing import Optional, List, Tuple
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from backend.api.database import get_db
from backend.api.models import Item, ItemAgentMetadata

router = APIRouter(prefix="/inbox", tags=["inbox"])


class EmailUpdate(BaseModel):
    read: Optional[bool] = None
    archived: Optional[bool] = None


class EmailSend(BaseModel):
    to: str
    subject: str
    body: str
    in_reply_to: Optional[str] = None


@router.get("")
async def get_inbox_items(
    filter: Optional[str] = Query(
        None,
        description=(
            "Filter: all, critical, high, deadline, "
            "primary, promotions, social, updates, forums, "
            "sent, spam, trash, drafts, inbox"
        ),
    ),
    cursor: Optional[str] = Query(
        None,
        description="Pagination cursor: ISO datetime string of last received_at; returns items before this",
    ),
    page_size: int = Query(50, description="Page size (max 200)"),
    db: Session = Depends(get_db),
):
    """Get inbox items with optional filtering (importance + Gmail-style folders/categories)."""
    page_size = min(max(page_size, 1), 200)

    def get_gmail_labels(item: Item) -> List[str]:
        if not item.raw_metadata or not isinstance(item.raw_metadata, dict):
            return []
        gmail_meta = item.raw_metadata.get("gmail")
        if not gmail_meta or not isinstance(gmail_meta, dict):
            return []
        labels = gmail_meta.get("labels", [])
        return labels if isinstance(labels, list) else []

    def classify_gmail_category(labels: List[str]) -> str:
        if "CATEGORY_PROMOTIONS" in labels:
            return "promotions"
        if "CATEGORY_SOCIAL" in labels:
            return "social"
        if "CATEGORY_UPDATES" in labels:
            return "updates"
        if "CATEGORY_FORUMS" in labels:
            return "forums"
        # If none of the category labels are present, treat as primary inbox
        return "primary"

    def classify_folder(item: Item, labels: List[str]) -> str:
        if "SPAM" in labels:
            return "spam"
        if "TRASH" in labels:
            return "trash"
        if "SENT" in labels or item.source_type == "email_sent":
            return "sent"
        if "DRAFT" in labels or item.source_type == "email_draft":
            return "drafts"
        return "inbox"

    # Base query and importance-based filtering
    query = db.query(Item).options(joinedload(Item.agent_metadata)).filter(Item.is_archived.is_(False))

    if filter == "critical":
        query = query.join(ItemAgentMetadata).filter(ItemAgentMetadata.importance == "critical")
    elif filter == "high":
        query = query.join(ItemAgentMetadata).filter(ItemAgentMetadata.importance.in_(["critical", "high"]))
    elif filter == "deadline":
        query = query.join(ItemAgentMetadata).filter(ItemAgentMetadata.category == "deadline")
    else:
        query = query.outerjoin(ItemAgentMetadata)

    # Pagination by received_datetime
    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            query = query.filter(Item.received_datetime != None, Item.received_datetime < cursor_dt)  # noqa: E711
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid cursor format; must be ISO datetime")

    items: List[Item] = query.order_by(Item.received_datetime.desc()).limit(page_size).all()

    gmail_category_filters = {"primary", "promotions", "social", "updates", "forums"}
    folder_filters = {"sent", "spam", "trash", "drafts", "inbox"}

    filtered: List[Tuple[Item, str, str, List[str]]] = []

    for item in items:
        labels = get_gmail_labels(item)
        gmail_category = classify_gmail_category(labels)
        folder = classify_folder(item, labels)

        include = True
        if filter in gmail_category_filters:
            if filter == "primary":
                # Primary should not include sent/drafts/spam/trash
                include = gmail_category == "primary" and folder == "inbox"
            else:
                include = gmail_category == filter
        elif filter in folder_filters:
            if filter == "inbox":
                include = folder == "inbox"
            else:
                include = folder == filter

        if include:
            filtered.append((item, gmail_category, folder, labels))

    # If no Gmail-style filter was applied, keep all items but still annotate
    if filter not in gmail_category_filters and filter not in folder_filters:
        filtered = [
            (
                item,
                classify_gmail_category(get_gmail_labels(item)),
                classify_folder(item, get_gmail_labels(item)),
                get_gmail_labels(item),
            )
            for item in items
        ]

    next_cursor = None
    if len(items) == page_size:
        last_item = items[-1]
        if last_item.received_datetime:
            next_cursor = last_item.received_datetime.isoformat()

    return {
        "items": [
            {
                "id": str(item.id),
                "source_type": item.source_type,
                "title": item.title,
                "body_preview": item.body_preview,
                "sender": item.sender,
                "received_at": item.received_datetime.isoformat() if item.received_datetime else None,
                # Agent-assigned importance/category
                "importance": item.agent_metadata.importance if item.agent_metadata else "medium",
                "category": item.agent_metadata.category if item.agent_metadata else None,
                "due_datetime": (
                    item.agent_metadata.due_datetime.isoformat()
                    if item.agent_metadata and item.agent_metadata.due_datetime
                    else None
                ),
                "suggested_action": item.agent_metadata.action_type if item.agent_metadata else None,
                "read": item.is_read,
                # Gmail-derived annotations
                "gmail_category": gmail_category,
                "folder": folder,
                "gmail_labels": labels,
            }
            for item, gmail_category, folder, labels in filtered
        ],
        "next_cursor": next_cursor,
    }


@router.get("/{item_id}")
async def get_inbox_item(item_id: str, db: Session = Depends(get_db)):
    """Get a single inbox item by ID."""
    item = db.query(Item).options(joinedload(Item.agent_metadata)).filter(Item.id == item_id).first()

    if not item:
        return {"error": "Item not found"}, 404

    gmail_meta = {}
    gmail_labels: List[str] = []
    calendar_meta = {}
    if item.raw_metadata and isinstance(item.raw_metadata, dict):
        raw_gmail = item.raw_metadata.get("gmail") or {}
        if isinstance(raw_gmail, dict):
            gmail_meta = {
                "message_id": raw_gmail.get("message_id"),
                "thread_id": raw_gmail.get("thread_id"),
            }
            labels_val = raw_gmail.get("labels", [])
            if isinstance(labels_val, list):
                gmail_labels = labels_val
            # Calendar info if present
            if raw_gmail.get("calendar_parsed"):
                calendar_meta = raw_gmail.get("calendar_parsed")
            elif raw_gmail.get("calendar_body"):
                calendar_meta = {"raw": raw_gmail.get("calendar_body")}

    return {
        "id": str(item.id),
        "source_type": item.source_type,
        "title": item.title,
        "body_full": item.body_full,
        "body_preview": item.body_preview,
        "sender": item.sender,
        "received_at": item.received_datetime.isoformat() if item.received_datetime else None,
        "importance": item.agent_metadata.importance if item.agent_metadata else "medium",
        "category": item.agent_metadata.category if item.agent_metadata else None,
        "due_datetime": (
            item.agent_metadata.due_datetime.isoformat()
            if item.agent_metadata and item.agent_metadata.due_datetime
            else None
        ),
        "suggested_action": item.agent_metadata.action_type if item.agent_metadata else None,
        "labels": item.agent_metadata.labels if item.agent_metadata else [],
        "gmail": gmail_meta,
        "gmail_labels": gmail_labels,
        "calendar": calendar_meta,
        "read": item.is_read,
    }


@router.patch("/{item_id}")
async def update_inbox_item(item_id: str, update: EmailUpdate, db: Session = Depends(get_db)):
    """Update an inbox item (mark as read, archive, etc.)."""
    item = db.query(Item).filter(Item.id == item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if update.read is not None:
        item.is_read = update.read
    if update.archived is not None:
        item.is_archived = update.archived

    db.commit()
    db.refresh(item)

    return {"success": True, "id": str(item.id)}


@router.delete("/{item_id}")
async def delete_inbox_item(item_id: str, db: Session = Depends(get_db)):
    """Delete an inbox item."""
    item = db.query(Item).filter(Item.id == item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()

    return {"success": True, "id": item_id}


@router.post("/send")
async def send_email(email: EmailSend, db: Session = Depends(get_db)):
    """Send an email (currently just stores as outgoing item)."""
    # For now, create an Item record for the sent email
    # In a real implementation, this would integrate with an email service

    new_item = Item(
        source_type="email_sent",
        title=email.subject,
        body_full=email.body,
        body_preview=email.body[:200] if len(email.body) > 200 else email.body,
        sender="me",
        received_datetime=datetime.utcnow(),
        is_read=True,
        is_archived=False,
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return {"success": True, "id": str(new_item.id), "message": "Email sent successfully"}
