"""
Dashboard API routes with proactive insights.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.api.database import get_db
from backend.api.models import Item, ItemAgentMetadata, ActionProposal, ConnectedAccount, AgentRunLog, User
from orchestrator.insights import (
    get_insight_engine,
    InsightCategory,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get aggregated dashboard statistics."""
    user = db.query(User).first()
    if not user:
        return {
            "total_items": 0,
            "items_by_provider": {},
            "items_by_importance": {},
            "items_by_category": {},
            "pending_actions": 0,
            "agent_stats": {
                "total_runs": 0,
                "success_rate": 0,
                "avg_duration_ms": 0,
                "runs_by_agent": {},
                "recent_runs": [],
            },
            "connected_accounts": 0,
            "recent_sync_activity": [],
        }

    user_id = user.id

    # Total items
    try:
        total_items = db.query(Item).filter(Item.user_id == user_id, Item.is_archived.is_(False)).count()
    except Exception:
        total_items = 0

    # Items by source_provider
    try:
        items_by_provider = (
            db.query(Item.source_provider, func.count(Item.id))
            .filter(Item.user_id == user_id, Item.is_archived.is_(False))
            .group_by(Item.source_provider)
            .all()
        )
        items_by_provider_dict = {provider: count for provider, count in items_by_provider}
    except Exception:
        items_by_provider_dict = {}

    # Items by importance
    try:
        items_by_importance = (
            db.query(ItemAgentMetadata.importance, func.count(ItemAgentMetadata.id))
            .join(Item)
            .filter(Item.user_id == user_id, Item.is_archived.is_(False))
            .group_by(ItemAgentMetadata.importance)
            .all()
        )
        items_by_importance_dict = {importance: count for importance, count in items_by_importance}
    except Exception:
        items_by_importance_dict = {}

    # Items by category
    try:
        items_by_category = (
            db.query(ItemAgentMetadata.category, func.count(ItemAgentMetadata.id))
            .join(Item)
            .filter(Item.user_id == user_id, Item.is_archived.is_(False), ItemAgentMetadata.category.isnot(None))
            .group_by(ItemAgentMetadata.category)
            .all()
        )
        items_by_category_dict = {category: count for category, count in items_by_category}
    except Exception:
        items_by_category_dict = {}

    # Pending actions
    try:
        pending_actions = (
            db.query(ActionProposal)
            .filter(ActionProposal.user_id == user_id, ActionProposal.status == "pending")
            .count()
        )
    except Exception:
        pending_actions = 0

    # Agent run statistics
    try:
        recent_runs = (
            db.query(AgentRunLog)
            .filter(AgentRunLog.user_id == user_id)
            .order_by(AgentRunLog.created_at.desc())
            .limit(100)
            .all()
        )

        total_runs = len(recent_runs)
        successful_runs = sum(1 for run in recent_runs if run.status == "success")
        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0

        avg_duration = (
            db.query(func.avg(AgentRunLog.duration_ms))
            .filter(AgentRunLog.user_id == user_id, AgentRunLog.duration_ms.isnot(None))
            .scalar()
            or 0
        )

        # Agent runs by agent_name
        agent_runs_by_name = (
            db.query(AgentRunLog.agent_name, func.count(AgentRunLog.id))
            .filter(AgentRunLog.user_id == user_id)
            .group_by(AgentRunLog.agent_name)
            .all()
        )
        agent_runs_dict = {agent_name: count for agent_name, count in agent_runs_by_name}

        agent_stats = {
            "total_runs": total_runs,
            "success_rate": round(success_rate, 2),
            "avg_duration_ms": round(float(avg_duration), 2) if avg_duration else 0,
            "runs_by_agent": agent_runs_dict,
            "recent_runs": [
                {
                    "id": str(run.id),
                    "agent_name": run.agent_name,
                    "context": run.context,
                    "status": run.status,
                    "duration_ms": run.duration_ms,
                    "created_at": run.created_at.isoformat() if run.created_at else None,
                }
                for run in recent_runs[:10]
            ],
        }
    except Exception:
        # If agent stats fail, return empty stats
        agent_stats = {
            "total_runs": 0,
            "success_rate": 0,
            "avg_duration_ms": 0,
            "runs_by_agent": {},
            "recent_runs": [],
        }

    # Connected accounts
    try:
        connected_accounts = (
            db.query(ConnectedAccount)
            .filter(ConnectedAccount.user_id == user_id, ConnectedAccount.status == "active")
            .count()
        )
    except Exception:
        connected_accounts = 0

    # Recent sync activity (last 7 days)
    try:
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_syncs = (
            db.query(AgentRunLog)
            .filter(
                AgentRunLog.user_id == user_id,
                AgentRunLog.context.in_(["refresh_inbox", "refresh_calendar", "sync_gmail", "sync_calendar"]),
                AgentRunLog.created_at >= seven_days_ago,
            )
            .order_by(AgentRunLog.created_at.desc())
            .limit(20)
            .all()
        )

        recent_sync_activity = [
            {
                "id": str(sync.id),
                "context": sync.context,
                "status": sync.status,
                "created_at": sync.created_at.isoformat() if sync.created_at else None,
            }
            for sync in recent_syncs
        ]
    except Exception:
        recent_sync_activity = []

    return {
        "total_items": total_items,
        "items_by_provider": items_by_provider_dict,
        "items_by_importance": items_by_importance_dict,
        "items_by_category": items_by_category_dict,
        "pending_actions": pending_actions,
        "agent_stats": agent_stats,
        "connected_accounts": connected_accounts,
        "recent_sync_activity": recent_sync_activity,
    }


# ============================================================================
# Insights API
# ============================================================================


@router.get("/insights")
async def get_insights(
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by minimum priority"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get proactive insights for the user.

    Insights include:
    - Calendar alerts (upcoming meetings, schedule gaps)
    - Weather alerts (especially for outdoor events)
    - Email notifications (important unread messages)
    - Priority reminders
    """
    user = db.query(User).first()
    if not user:
        return {"insights": [], "total": 0}

    try:
        engine = get_insight_engine()

        # Gather data for insight generation
        calendar_events = await _get_todays_events(db, user.id)
        current_weather = await _get_current_weather(user)
        weather_forecast = await _get_weather_forecast(user)
        recent_emails = await _get_recent_emails(db, user.id)
        unread_count = await _get_unread_count(db, user.id)

        # Generate insights
        insights = await engine.generate_insights(
            calendar_events=calendar_events,
            current_weather=current_weather,
            weather_forecast=weather_forecast,
            recent_emails=recent_emails,
            unread_email_count=unread_count,
        )

        # Filter by category if specified
        if category:
            try:
                cat = InsightCategory(category)
                insights = [i for i in insights if i.category == cat]
            except ValueError:
                pass

        # Filter by minimum priority if specified
        if priority:
            priority_order = {
                "critical": 0,
                "high": 1,
                "medium": 2,
                "low": 3,
            }
            min_priority = priority_order.get(priority.lower(), 3)
            insights = [i for i in insights if priority_order.get(i.priority.value, 4) <= min_priority]

        # Apply limit
        limited_insights = insights[:limit]

        return {
            "insights": [i.model_dump() for i in limited_insights],
            "total": len(insights),
            "filtered": len(limited_insights) < len(insights),
        }

    except Exception as e:
        logger.error(f"Error generating insights: {e}", exc_info=True)
        return {"insights": [], "total": 0, "error": str(e)}


@router.get("/briefing")
async def get_morning_briefing(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get a comprehensive morning briefing.

    Includes:
    - Personalized greeting
    - Today's schedule overview
    - Weather summary
    - Top priorities
    - Key insights
    - Suggested focus for the day
    """
    user = db.query(User).first()
    if not user:
        return {
            "greeting": "Hello!",
            "date_summary": datetime.now().strftime("%A, %B %d"),
            "weather_summary": None,
            "calendar_summary": "No calendar data available",
            "priority_summary": "Set up your account to see priorities",
            "email_summary": None,
            "insights": [],
            "suggested_focus": "Start by connecting your accounts",
        }

    try:
        engine = get_insight_engine()

        # Gather data
        calendar_events = await _get_todays_events(db, user.id)
        current_weather = await _get_current_weather(user)
        weather_forecast = await _get_weather_forecast(user)
        recent_emails = await _get_recent_emails(db, user.id)
        unread_count = await _get_unread_count(db, user.id)
        priorities = await _get_priorities(db, user.id)

        # Generate briefing
        briefing = await engine.generate_morning_briefing(
            user_name=user.display_name,
            calendar_events=calendar_events,
            current_weather=current_weather,
            weather_forecast=weather_forecast,
            recent_emails=recent_emails,
            unread_email_count=unread_count,
            priorities=priorities,
        )

        return briefing.model_dump()

    except Exception as e:
        logger.error(f"Error generating briefing: {e}", exc_info=True)
        return {
            "greeting": "Hello!",
            "date_summary": datetime.now().strftime("%A, %B %d"),
            "error": str(e),
            "weather_summary": None,
            "calendar_summary": "Error loading calendar",
            "priority_summary": "Error loading priorities",
            "email_summary": None,
            "insights": [],
            "suggested_focus": "Please try again later",
        }


@router.post("/insights/{insight_id}/dismiss")
async def dismiss_insight(insight_id: str) -> Dict[str, bool]:
    """Dismiss an insight so it won't show again."""
    engine = get_insight_engine()
    success = engine.dismiss_insight(insight_id)
    return {"success": success}


# ============================================================================
# Helper Functions for Data Gathering
# ============================================================================


async def _get_todays_events(db: Session, user_id) -> List[Dict[str, Any]]:
    """Get today's calendar events."""
    try:
        today = datetime.now().date()

        events = (
            db.query(Item)
            .filter(
                Item.user_id == user_id,
                Item.item_type == "event",
                Item.is_archived.is_(False),
            )
            .all()
        )

        # Filter for today's events
        today_events = []
        for event in events:
            if event.raw_data:
                start = event.raw_data.get("start", {})
                start_time = start.get("dateTime", start.get("date", ""))
                if start_time:
                    try:
                        if "T" in start_time:
                            event_date = datetime.fromisoformat(start_time.replace("Z", "+00:00")).date()
                        else:
                            event_date = datetime.strptime(start_time, "%Y-%m-%d").date()

                        if event_date == today:
                            today_events.append(
                                {
                                    "id": str(event.id),
                                    "title": event.raw_data.get("summary", "Untitled Event"),
                                    "start": start_time,
                                    "end": event.raw_data.get("end", {}).get("dateTime", ""),
                                    "location": event.raw_data.get("location", ""),
                                    "meeting_link": event.raw_data.get("hangoutLink", ""),
                                }
                            )
                    except Exception:
                        pass

        return sorted(today_events, key=lambda e: e.get("start", ""))

    except Exception as e:
        logger.error(f"Error getting today's events: {e}")
        return []


async def _get_current_weather(user: User) -> Optional[Dict[str, Any]]:
    """Get current weather for user's location."""
    try:
        from backend.integrations.weather import WeatherService

        if not user.location:
            return None

        weather_service = WeatherService()
        return await weather_service.get_current_weather(user.location)

    except Exception as e:
        logger.debug(f"Weather not available: {e}")
        return None


async def _get_weather_forecast(user: User) -> Optional[List[Dict[str, Any]]]:
    """Get weather forecast for user's location."""
    try:
        from backend.integrations.weather import WeatherService

        if not user.location:
            return None

        weather_service = WeatherService()
        forecast = await weather_service.get_forecast(user.location, days=5)
        return forecast.get("daily", []) if forecast else None

    except Exception as e:
        logger.debug(f"Forecast not available: {e}")
        return None


async def _get_recent_emails(db: Session, user_id, limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent emails."""
    try:
        emails = (
            db.query(Item)
            .filter(
                Item.user_id == user_id,
                Item.item_type == "email",
                Item.is_archived.is_(False),
            )
            .order_by(Item.received_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": str(email.id),
                "sender": email.raw_data.get("from", "") if email.raw_data else "",
                "subject": email.raw_data.get("subject", "") if email.raw_data else "",
                "is_read": email.raw_data.get("is_read", True) if email.raw_data else True,
                "received_at": email.received_at.isoformat() if email.received_at else "",
            }
            for email in emails
        ]

    except Exception as e:
        logger.error(f"Error getting recent emails: {e}")
        return []


async def _get_unread_count(db: Session, user_id) -> int:
    """Get count of unread emails."""
    try:
        # This is a simplified count - in production would check raw_data.is_read
        return (
            db.query(Item)
            .filter(
                Item.user_id == user_id,
                Item.item_type == "email",
                Item.is_archived.is_(False),
            )
            .count()
        )
    except Exception:
        return 0


async def _get_priorities(db: Session, user_id, limit: int = 10) -> List[Dict[str, Any]]:
    """Get priority items."""
    try:
        priority_items = (
            db.query(Item, ItemAgentMetadata)
            .join(ItemAgentMetadata)
            .filter(
                Item.user_id == user_id,
                Item.is_archived.is_(False),
                ItemAgentMetadata.importance.in_(["critical", "high"]),
            )
            .order_by(
                ItemAgentMetadata.importance.desc(),
                Item.received_at.desc(),
            )
            .limit(limit)
            .all()
        )

        return [
            {
                "id": str(item.id),
                "title": item.raw_data.get("subject", item.raw_data.get("summary", "")) if item.raw_data else "",
                "importance": meta.importance,
                "category": meta.category,
            }
            for item, meta in priority_items
        ]

    except Exception as e:
        logger.error(f"Error getting priorities: {e}")
        return []
