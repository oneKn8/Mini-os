"""
Calendar API routes
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.database import get_db
from backend.api.models import Item, User, ConnectedAccount
from backend.api.sse import emit_calendar_update
from backend.integrations.calendar import CalendarClient

router = APIRouter(prefix="/calendar", tags=["calendar"])


class EventCreate(BaseModel):
    title: str
    start: datetime
    end: datetime
    description: Optional[str] = ""
    location: Optional[str] = ""


class EventUpdate(BaseModel):
    title: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    description: Optional[str] = None
    location: Optional[str] = None


def get_calendar_client(db: Session, user_id) -> Optional[CalendarClient]:
    """Get calendar client if user has connected account."""
    account = (
        db.query(ConnectedAccount)
        .filter(
            ConnectedAccount.user_id == user_id,
            ConnectedAccount.provider == "google_calendar",
            ConnectedAccount.status == "active",
        )
        .first()
    )

    if not account:
        return None

    return CalendarClient.from_tokens(
        access_token=account.access_token,
        refresh_token=account.refresh_token,
        token_uri=account.token_uri,
        client_id=account.client_id,
        client_secret=account.client_secret,
    )


@router.get("/events")
async def get_calendar_events(
    start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, db: Session = Depends(get_db)
):
    """Get calendar events."""
    # TODO: Get user from session/auth token
    user = db.query(User).first()
    if not user:
        return []

    # If start_date not provided, default to today
    if not start_date:
        start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # If end_date not provided, default to 30 days from start
    if not end_date:
        end_date = start_date + timedelta(days=30)

    # Query items from database first
    events = (
        db.query(Item)
        .filter(
            Item.user_id == user.id,
            Item.source_type == "event",
            Item.start_datetime >= start_date,
            Item.start_datetime <= end_date,
            Item.is_archived.is_(False),
        )
        .order_by(Item.start_datetime)
        .all()
    )

    return [
        {
            "id": str(event.id),
            "title": event.title,
            "description": event.body_preview,
            "start": event.start_datetime.isoformat() if event.start_datetime else None,
            "end": event.end_datetime.isoformat() if event.end_datetime else None,
            "location": event.raw_metadata.get("google_calendar", {}).get("location") if event.raw_metadata else None,
            "source_id": event.source_id,
        }
        for event in events
    ]


@router.post("/events")
async def create_calendar_event(event: EventCreate, db: Session = Depends(get_db)):
    """Create a new calendar event."""
    # TODO: Get user from session/auth token
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    client = get_calendar_client(db, user.id)
    if not client:
        raise HTTPException(status_code=400, detail="Google Calendar not connected")

    try:
        result = client.create_event(
            title=event.title, start=event.start, end=event.end, description=event.description, location=event.location
        )
        # Emit calendar update event
        await emit_calendar_update(
            "event_created",
            {
                "event_id": result.get("id"),
                "title": event.title,
                "start": event.start.isoformat(),
                "end": event.end.isoformat(),
            },
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")


@router.put("/events/{event_id}")
async def update_calendar_event(event_id: str, event: EventUpdate, db: Session = Depends(get_db)):
    """Update a calendar event."""
    # TODO: Get user from session/auth token
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Check if event exists in DB to get source_id
    # Note: event_id passed here is likely the DB UUID or the source_id.
    # Ideally we accept DB ID and look up source_id
    item = db.query(Item).filter(Item.id == event_id, Item.user_id == user.id).first()

    if not item:
        # Try treating event_id as source_id (Google ID)
        item = db.query(Item).filter(Item.source_id == event_id, Item.user_id == user.id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Event not found")

    client = get_calendar_client(db, user.id)
    if not client:
        raise HTTPException(status_code=400, detail="Google Calendar not connected")

    updates = {}
    if event.title:
        updates["summary"] = event.title
    if event.description:
        updates["description"] = event.description
    if event.location:
        updates["location"] = event.location
    if event.start:
        updates["start"] = {"dateTime": event.start.isoformat(), "timeZone": "UTC"}
    if event.end:
        updates["end"] = {"dateTime": event.end.isoformat(), "timeZone": "UTC"}

    try:
        result = client.update_event(item.source_id, **updates)
        # Emit calendar update event
        await emit_calendar_update(
            "event_updated",
            {
                "event_id": event_id,
                "updates": updates,
            },
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update event: {str(e)}")


@router.delete("/events/{event_id}")
async def delete_calendar_event(event_id: str, db: Session = Depends(get_db)):
    """Delete a calendar event."""
    # TODO: Get user from session/auth token
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    item = db.query(Item).filter(Item.id == event_id, Item.user_id == user.id).first()
    if not item:
        # Try treating as source_id
        item = db.query(Item).filter(Item.source_id == event_id, Item.user_id == user.id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Event not found")

    client = get_calendar_client(db, user.id)
    if not client:
        raise HTTPException(status_code=400, detail="Google Calendar not connected")

    try:
        client.delete_event(item.source_id)

        # Also mark as archived/deleted in DB
        item.is_archived = True
        db.commit()

        # Emit calendar update event
        await emit_calendar_update(
            "event_deleted",
            {
                "event_id": event_id,
            },
        )

        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete event: {str(e)}")
