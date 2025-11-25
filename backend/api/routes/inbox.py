"""
Inbox API routes
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.api.database import get_db
from backend.api.models import Item

router = APIRouter(prefix="/inbox", tags=["inbox"])


@router.get("")
async def get_inbox_items(
    filter: Optional[str] = Query(None, description="Filter: all, critical, high, deadline"),
    db: Session = Depends(get_db),
):
    """Get inbox items with optional filtering."""
    query = db.query(Item).filter(Item.ingestion_status == "processed")

    if filter == "critical":
        query = query.filter(Item.importance == "critical")
    elif filter == "high":
        query = query.filter(Item.importance.in_(["critical", "high"]))
    elif filter == "deadline":
        query = query.filter(Item.category == "deadline")

    items = query.order_by(Item.received_at.desc()).limit(100).all()

    return [
        {
            "id": str(item.id),
            "source_type": item.source_type,
            "title": item.title,
            "body_preview": item.body_preview,
            "sender": item.sender,
            "received_at": item.received_at.isoformat(),
            "importance": item.importance,
            "category": item.category,
            "due_datetime": item.due_datetime.isoformat() if item.due_datetime else None,
            "suggested_action": item.suggested_action,
        }
        for item in items
    ]


@router.get("/{item_id}")
async def get_inbox_item(item_id: str, db: Session = Depends(get_db)):
    """Get a single inbox item by ID."""
    item = db.query(Item).filter(Item.id == item_id).first()

    if not item:
        return {"error": "Item not found"}, 404

    return {
        "id": str(item.id),
        "source_type": item.source_type,
        "title": item.title,
        "body_full": item.body_full,
        "body_preview": item.body_preview,
        "sender": item.sender,
        "received_at": item.received_at.isoformat(),
        "importance": item.importance,
        "category": item.category,
        "due_datetime": item.due_datetime.isoformat() if item.due_datetime else None,
        "suggested_action": item.suggested_action,
        "labels": item.labels,
    }
