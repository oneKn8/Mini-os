"""
Inbox API routes
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from backend.api.database import get_db
from backend.api.models import Item, ItemAgentMetadata

router = APIRouter(prefix="/inbox", tags=["inbox"])


@router.get("")
async def get_inbox_items(
    filter: Optional[str] = Query(None, description="Filter: all, critical, high, deadline"),
    db: Session = Depends(get_db),
):
    """Get inbox items with optional filtering."""
    query = db.query(Item).options(joinedload(Item.agent_metadata)).filter(Item.is_archived == False)

    if filter == "critical":
        query = query.join(ItemAgentMetadata).filter(ItemAgentMetadata.importance == "critical")
    elif filter == "high":
        query = query.join(ItemAgentMetadata).filter(ItemAgentMetadata.importance.in_(["critical", "high"]))
    elif filter == "deadline":
        query = query.join(ItemAgentMetadata).filter(ItemAgentMetadata.category == "deadline")
    else:
        # For other filters, still join to access metadata
        query = query.outerjoin(ItemAgentMetadata)

    items = query.order_by(Item.received_datetime.desc()).limit(100).all()

    return [
        {
            "id": str(item.id),
            "source_type": item.source_type,
            "title": item.title,
            "body_preview": item.body_preview,
            "sender": item.sender,
            "received_at": item.received_datetime.isoformat() if item.received_datetime else None,
            "importance": item.agent_metadata.importance if item.agent_metadata else "medium",
            "category": item.agent_metadata.category if item.agent_metadata else None,
            "due_datetime": item.agent_metadata.due_datetime.isoformat()
            if item.agent_metadata and item.agent_metadata.due_datetime
            else None,
            "suggested_action": item.agent_metadata.action_type if item.agent_metadata else None,
        }
        for item in items
    ]


@router.get("/{item_id}")
async def get_inbox_item(item_id: str, db: Session = Depends(get_db)):
    """Get a single inbox item by ID."""
    item = db.query(Item).options(joinedload(Item.agent_metadata)).filter(Item.id == item_id).first()

    if not item:
        return {"error": "Item not found"}, 404

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
        "due_datetime": item.agent_metadata.due_datetime.isoformat()
        if item.agent_metadata and item.agent_metadata.due_datetime
        else None,
        "suggested_action": item.agent_metadata.action_type if item.agent_metadata else None,
        "labels": item.agent_metadata.labels if item.agent_metadata else [],
    }
