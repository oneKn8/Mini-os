"""
Calendar tools for the conversational agent.

Provides tools for querying and managing calendar events.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CalendarEvent(BaseModel):
    """A calendar event."""

    id: str = Field(description="Event ID")
    title: str = Field(description="Event title")
    start: str = Field(description="Start datetime ISO format")
    end: str = Field(description="End datetime ISO format")
    location: Optional[str] = Field(description="Event location", default=None)
    description: Optional[str] = Field(description="Event description", default=None)
    is_all_day: bool = Field(description="Whether it's an all-day event", default=False)


class CalendarEventOutput(BaseModel):
    """Output schema for calendar queries."""

    events: List[CalendarEvent] = Field(description="List of calendar events", default_factory=list)
    summary: str = Field(description="Summary of events")
    date_range: str = Field(description="Date range covered")


class CreateEventOutput(BaseModel):
    """Output schema for event creation."""

    success: bool = Field(description="Whether the event was created")
    event_id: Optional[str] = Field(description="Created event ID", default=None)
    message: str = Field(description="Status message")
    requires_approval: bool = Field(description="Whether this action requires user approval", default=True)
    proposal_id: Optional[str] = Field(description="Action proposal ID if approval needed", default=None)


def _get_db_session():
    """Get a database session."""
    from backend.api.database import SessionLocal

    return SessionLocal()


def _get_events_from_db(start_date: datetime, end_date: datetime, limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch events from database within date range."""
    try:
        from backend.api.models import Item

        db = _get_db_session()
        try:
            events = (
                db.query(Item)
                .filter(
                    Item.source_type == "event", Item.start_datetime >= start_date, Item.start_datetime <= end_date
                )
                .order_by(Item.start_datetime.asc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "id": str(e.id),
                    "title": e.title or "Untitled Event",
                    "start": e.start_datetime.isoformat() if e.start_datetime else None,
                    "end": e.end_datetime.isoformat() if e.end_datetime else None,
                    "location": e.raw_metadata.get("location") if e.raw_metadata else None,
                    "description": e.body_preview,
                }
                for e in events
            ]
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to fetch events: {e}")
        return []


@tool
def get_todays_events() -> CalendarEventOutput:
    """
    Get all calendar events for today.

    Returns a list of today's events with times and locations.

    Returns:
        Today's calendar events
    """
    now = datetime.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    events_data = _get_events_from_db(start_of_day, end_of_day)

    events = []
    for e in events_data:
        if e.get("start"):
            events.append(
                CalendarEvent(
                    id=e["id"],
                    title=e["title"],
                    start=e["start"],
                    end=e.get("end") or e["start"],
                    location=e.get("location"),
                    description=e.get("description"),
                )
            )

    if not events:
        summary = "You have no events scheduled for today. Your calendar is clear!"
    elif len(events) == 1:
        summary = f"You have 1 event today: {events[0].title}"
    else:
        summary = f"You have {len(events)} events today."
        # Add time info for first few
        for event in events[:3]:
            try:
                start_dt = datetime.fromisoformat(event.start)
                summary += f" {event.title} at {start_dt.strftime('%I:%M %p')}."
            except Exception:
                pass

    return CalendarEventOutput(events=events, summary=summary, date_range=f"Today ({now.strftime('%B %d, %Y')})")


@tool
def get_upcoming_events(days_ahead: int = 7, limit: int = 20) -> CalendarEventOutput:
    """
    Get upcoming calendar events for the next several days.

    Args:
        days_ahead: Number of days to look ahead (default: 7)
        limit: Maximum number of events to return (default: 20)

    Returns:
        Upcoming calendar events within the specified range
    """
    now = datetime.now()
    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=days_ahead)

    events_data = _get_events_from_db(start_date, end_date, limit=limit)

    events = []
    events_by_day: Dict[str, int] = {}

    for e in events_data:
        if e.get("start"):
            events.append(
                CalendarEvent(
                    id=e["id"],
                    title=e["title"],
                    start=e["start"],
                    end=e.get("end") or e["start"],
                    location=e.get("location"),
                    description=e.get("description"),
                )
            )
            # Count by day
            try:
                day = datetime.fromisoformat(e["start"]).strftime("%A")
                events_by_day[day] = events_by_day.get(day, 0) + 1
            except Exception:
                pass

    if not events:
        summary = f"No events scheduled for the next {days_ahead} days."
    else:
        summary = f"You have {len(events)} events in the next {days_ahead} days."
        # Add busiest day info
        if events_by_day:
            busiest_day = max(events_by_day.items(), key=lambda x: x[1])
            summary += f" Busiest day: {busiest_day[0]} with {busiest_day[1]} event(s)."

    return CalendarEventOutput(
        events=events, summary=summary, date_range=f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
    )


@tool
def create_calendar_event(
    title: str,
    start_time: str,
    end_time: Optional[str] = None,
    duration_minutes: int = 60,
    location: Optional[str] = None,
    description: Optional[str] = None,
) -> CreateEventOutput:
    """
    Create a new calendar event.

    This action requires user approval before execution.

    Args:
        title: Event title
        start_time: Start time in ISO format or natural language (e.g., "tomorrow at 2pm")
        end_time: End time (optional, calculated from duration if not provided)
        duration_minutes: Duration in minutes (default: 60)
        location: Event location (optional)
        description: Event description (optional)

    Returns:
        Status of the event creation request
    """
    try:
        from backend.api.models import ActionProposal, User
        import uuid

        # Parse start time
        try:
            start_dt = datetime.fromisoformat(start_time)
        except ValueError:
            # Try to parse natural language dates
            now = datetime.now()
            if "tomorrow" in start_time.lower():
                start_dt = now + timedelta(days=1)
                start_dt = start_dt.replace(hour=9, minute=0, second=0, microsecond=0)
            else:
                start_dt = now + timedelta(hours=1)

        # Calculate end time
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time)
            except ValueError:
                end_dt = start_dt + timedelta(minutes=duration_minutes)
        else:
            end_dt = start_dt + timedelta(minutes=duration_minutes)

        db = _get_db_session()
        try:
            # Get user
            user = db.query(User).first()
            if not user:
                return CreateEventOutput(success=False, message="No user account found", requires_approval=False)

            # Create action proposal
            proposal = ActionProposal(
                id=uuid.uuid4(),
                user_id=user.id,
                agent_name="conversational_agent",
                action_type="create_calendar_event",
                payload={
                    "title": title,
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                    "location": location,
                    "description": description,
                    "provider": "google_calendar",
                },
                status="pending",
                risk_level="low",
                explanation=f"Create event '{title}' on {start_dt.strftime('%B %d at %I:%M %p')}",
            )
            db.add(proposal)
            db.commit()

            return CreateEventOutput(
                success=True,
                event_id=None,  # Will be set after execution
                message=f"Event '{title}' proposal created. Awaiting your approval.",
                requires_approval=True,
                proposal_id=str(proposal.id),
            )

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to create event proposal: {e}")
        return CreateEventOutput(success=False, message=f"Failed to create event: {str(e)}", requires_approval=False)
