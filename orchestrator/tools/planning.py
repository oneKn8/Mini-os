"""
Planning tools for the conversational agent.

Provides tools for daily planning, priority analysis, and task organization.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TimeBlock(BaseModel):
    """A suggested time block for a task."""

    task: str = Field(description="Name of the task")
    suggested_time: str = Field(description="Suggested start time (HH:MM format)")
    duration_minutes: int = Field(description="Duration in minutes")
    priority: str = Field(description="Priority level: high, medium, low")


class PlanDayOutput(BaseModel):
    """Output schema for the plan_day tool."""

    must_do_today: List[str] = Field(
        description="Top 3-5 most important items that must be done today", default_factory=list
    )
    focus_areas: List[str] = Field(description="Key areas to focus on", default_factory=list)
    time_blocks: List[TimeBlock] = Field(description="Suggested time blocks for focused work", default_factory=list)
    considerations: str = Field(description="Important considerations like weather, meetings, deadlines", default="")
    reasoning: str = Field(description="Brief explanation of why this plan makes sense", default="")


class PriorityItemsOutput(BaseModel):
    """Output schema for priority items."""

    critical: List[Dict[str, Any]] = Field(
        description="Critical priority items requiring immediate attention", default_factory=list
    )
    high: List[Dict[str, Any]] = Field(description="High priority items for today", default_factory=list)
    medium: List[Dict[str, Any]] = Field(description="Medium priority items", default_factory=list)
    summary: str = Field(description="Brief summary of priorities", default="")


def _get_db_session():
    """Get a database session."""
    from backend.api.database import SessionLocal

    return SessionLocal()


def _get_items_from_db(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch recent items from database."""
    try:
        from backend.api.models import Item

        db = _get_db_session()
        try:
            items = db.query(Item).order_by(Item.created_at.desc()).limit(limit).all()
            result = []
            for item in items:
                metadata = item.agent_metadata
                result.append(
                    {
                        "id": str(item.id),
                        "title": item.title or "",
                        "body_preview": item.body_preview or "",
                        "source_type": item.source_type or "email",
                        "sender": item.sender or "",
                        "importance": getattr(metadata, "importance", "medium") if metadata else "medium",
                        "category": getattr(metadata, "category", "other") if metadata else "other",
                        "due_datetime": (
                            metadata.due_datetime.isoformat() if (metadata and metadata.due_datetime) else None
                        ),
                    }
                )
            return result
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to fetch items: {e}")
        return []


def _get_events_from_db(days_ahead: int = 1) -> List[Dict[str, Any]]:
    """Fetch upcoming events from database."""
    try:
        from backend.api.models import Item

        db = _get_db_session()
        try:
            now = datetime.now()
            end_date = now + timedelta(days=days_ahead)
            events = (
                db.query(Item)
                .filter(Item.source_type == "event", Item.start_datetime >= now, Item.start_datetime <= end_date)
                .order_by(Item.start_datetime.asc())
                .all()
            )

            return [
                {
                    "id": str(e.id),
                    "title": e.title or "",
                    "start": e.start_datetime.isoformat() if e.start_datetime else None,
                    "end": e.end_datetime.isoformat() if e.end_datetime else None,
                }
                for e in events
            ]
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to fetch events: {e}")
        return []


@tool
def plan_day(include_weather: bool = True, focus_hours: Optional[int] = None) -> PlanDayOutput:
    """
    Create a daily plan based on inbox items, calendar events, and priorities.

    This tool analyzes the user's emails, events, and tasks to create
    an actionable plan for the day with suggested time blocks.

    Args:
        include_weather: Whether to consider weather in planning (default: True)
        focus_hours: Target number of focus hours to schedule (default: auto-detect)

    Returns:
        A structured daily plan with must-do items, focus areas, and time blocks
    """
    from orchestrator.llm_client import LLMClient

    # Gather context
    items = _get_items_from_db(limit=50)
    events = _get_events_from_db(days_ahead=1)

    if not items and not events:
        return PlanDayOutput(
            must_do_today=["Check your inbox for new items"],
            focus_areas=["Getting started"],
            time_blocks=[],
            considerations="No items or events found. Connect your accounts to get personalized planning.",
            reasoning="Unable to create a detailed plan without inbox data.",
        )

    # Filter high priority items
    critical_items = [i for i in items if i.get("importance") in ["critical", "high"]]

    # Build context for LLM
    now = datetime.now()
    context = {
        "current_time": now.strftime("%Y-%m-%d %H:%M"),
        "day_of_week": now.strftime("%A"),
        "total_items": len(items),
        "critical_items": len(critical_items),
        "events_today": len(events),
        "items_sample": critical_items[:10] if critical_items else items[:10],
        "events": events[:5],
    }

    # Use LLM to create the plan
    try:
        llm = LLMClient()
        prompt = f"""You are a personal productivity assistant. Create a daily plan.

Context:
- Current time: {context['current_time']} ({context['day_of_week']})
- Total inbox items: {context['total_items']}
- High priority items: {context['critical_items']}
- Events today: {context['events_today']}

High Priority Items:
{json.dumps(context['items_sample'], indent=2)}

Today's Events:
{json.dumps(context['events'], indent=2)}

Create a focused, realistic daily plan. Respond with JSON:
{{
    "must_do_today": ["item1", "item2", "item3"],
    "focus_areas": ["area1", "area2"],
    "time_blocks": [
        {{"task": "task name", "suggested_time": "09:00", "duration_minutes": 60, "priority": "high"}}
    ],
    "considerations": "Any important notes about weather, conflicts, etc.",
    "reasoning": "Why this plan makes sense"
}}

Keep it realistic - max 3-5 must-do items. Focus on what's achievable."""

        result = llm.call_json(prompt, temperature=0.3)

        # Parse time blocks
        time_blocks = []
        for tb in result.get("time_blocks", []):
            time_blocks.append(
                TimeBlock(
                    task=tb.get("task", "Work block"),
                    suggested_time=tb.get("suggested_time", "09:00"),
                    duration_minutes=tb.get("duration_minutes", 60),
                    priority=tb.get("priority", "medium"),
                )
            )

        return PlanDayOutput(
            must_do_today=result.get("must_do_today", [])[:5],
            focus_areas=result.get("focus_areas", [])[:3],
            time_blocks=time_blocks[:5],
            considerations=result.get("considerations", ""),
            reasoning=result.get("reasoning", "Plan created based on your inbox and calendar."),
        )

    except Exception as e:
        logger.error(f"LLM planning failed: {e}")
        # Fallback to simple priority-based plan
        must_do = [item.get("title", "Task") for item in critical_items[:3]]
        if not must_do:
            must_do = [item.get("title", "Task") for item in items[:3]]

        return PlanDayOutput(
            must_do_today=must_do,
            focus_areas=["High priority tasks"],
            time_blocks=[],
            considerations="",
            reasoning="Basic plan based on item priorities.",
        )


@tool
def get_priority_items(importance_filter: Optional[str] = None, limit: int = 10) -> PriorityItemsOutput:
    """
    Get items organized by priority level.

    Args:
        importance_filter: Filter by importance level (critical, high, medium, low)
        limit: Maximum number of items per category

    Returns:
        Items grouped by priority level
    """
    items = _get_items_from_db(limit=100)

    critical = []
    high = []
    medium = []

    for item in items:
        importance = item.get("importance", "medium")
        item_data = {
            "id": item.get("id"),
            "title": item.get("title"),
            "category": item.get("category"),
            "due": item.get("due_datetime"),
        }

        if importance_filter and importance != importance_filter:
            continue

        if importance == "critical":
            if len(critical) < limit:
                critical.append(item_data)
        elif importance == "high":
            if len(high) < limit:
                high.append(item_data)
        elif importance == "medium":
            if len(medium) < limit:
                medium.append(item_data)

    total_critical = len(critical)
    total_high = len(high)

    summary = f"Found {total_critical} critical and {total_high} high priority items."
    if total_critical > 0:
        summary += " Address critical items first."
    elif total_high > 0:
        summary += " Focus on high priority items today."
    else:
        summary += " No urgent items - good time for deep work."

    return PriorityItemsOutput(critical=critical, high=high, medium=medium, summary=summary)
