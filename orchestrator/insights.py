"""
Insight Engine - Proactive intelligence for the multi-agent system.

This module analyzes user data to proactively surface relevant insights:
- Calendar changes and reminders
- Weather alerts for outdoor events
- Important email patterns
- Morning briefings
- Cross-domain connections

Examples:
- "Heads up: Your 2pm meeting location changed"
- "You have 5 unread emails from your manager"
- "Weather alert: Rain expected during your outdoor event Friday"
- Morning briefing: "Good morning! Here's your day..."
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ============================================================================
# Insight Types and Schemas
# ============================================================================


class InsightCategory(str, Enum):
    """Categories of insights."""

    CALENDAR = "calendar"
    WEATHER = "weather"
    EMAIL = "email"
    PRIORITY = "priority"
    BRIEFING = "briefing"
    ALERT = "alert"
    REMINDER = "reminder"
    CONNECTION = "connection"


class InsightPriority(str, Enum):
    """Priority levels for insights."""

    CRITICAL = "critical"  # Requires immediate attention
    HIGH = "high"  # Important, should see soon
    MEDIUM = "medium"  # Worth knowing
    LOW = "low"  # Nice to know


class Insight(BaseModel):
    """A proactive insight to surface to the user."""

    id: str = Field(description="Unique identifier")
    category: InsightCategory = Field(description="Category of insight")
    priority: InsightPriority = Field(description="Priority level")
    title: str = Field(description="Short title for the insight")
    message: str = Field(description="Detailed message")
    icon: str = Field(description="Icon/emoji for display")
    source: str = Field(description="What generated this insight")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional data relevant to the insight")
    actions: List[Dict[str, str]] = Field(default_factory=list, description="Suggested actions the user can take")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = Field(default=None, description="When this insight is no longer relevant")
    dismissed: bool = Field(default=False)


class MorningBriefing(BaseModel):
    """A morning briefing summary."""

    greeting: str = Field(description="Personalized greeting")
    date_summary: str = Field(description="Today's date in friendly format")
    weather_summary: Optional[str] = Field(default=None)
    calendar_summary: str = Field(description="Overview of today's schedule")
    priority_summary: str = Field(description="Key priorities for today")
    email_summary: Optional[str] = Field(default=None)
    insights: List[Insight] = Field(default_factory=list, description="Notable insights for today")
    suggested_focus: str = Field(description="Suggested focus area for the day")


# ============================================================================
# Insight Generators
# ============================================================================


class CalendarInsightGenerator:
    """Generates insights from calendar data."""

    async def generate(
        self, events: List[Dict[str, Any]], historical_events: Optional[List[Dict[str, Any]]] = None
    ) -> List[Insight]:
        """Generate calendar-related insights."""
        insights = []
        now = datetime.now(timezone.utc)

        # Check for meetings in the next hour
        upcoming_soon = [e for e in events if self._is_within_hours(e.get("start"), 1)]

        for event in upcoming_soon:
            minutes_until = self._minutes_until(event.get("start"))
            if minutes_until and 0 < minutes_until <= 15:
                insights.append(
                    Insight(
                        id=f"cal_upcoming_{event.get('id', '')}",
                        category=InsightCategory.CALENDAR,
                        priority=InsightPriority.HIGH,
                        title="Meeting Starting Soon",
                        message=f"{event.get('title', 'Meeting')} starts in {minutes_until} minutes",
                        icon="calendar",
                        source="calendar",
                        data={"event": event},
                        actions=[
                            {"text": "View details", "action": "view_event", "payload": event.get("id", "")},
                            {"text": "Join meeting", "action": "join", "payload": event.get("meeting_link", "")},
                        ],
                        expires_at=self._parse_time(event.get("start")),
                    )
                )

        # Check for schedule gaps (potential focus time)
        gaps = self._find_schedule_gaps(events)
        if gaps:
            largest_gap = max(gaps, key=lambda g: g["duration"])
            if largest_gap["duration"] >= 60:  # At least 1 hour
                insights.append(
                    Insight(
                        id=f"cal_gap_{largest_gap['start'].isoformat()}",
                        category=InsightCategory.CALENDAR,
                        priority=InsightPriority.MEDIUM,
                        title="Focus Time Available",
                        message=f"You have {largest_gap['duration']} minutes free from {largest_gap['start'].strftime('%I:%M %p')}",
                        icon="target",
                        source="calendar",
                        data={"gap": largest_gap},
                        actions=[
                            {
                                "text": "Block for focus",
                                "action": "message",
                                "payload": "Block this time for focused work",
                            },
                        ],
                        expires_at=largest_gap["end"],
                    )
                )

        # Check for back-to-back meetings
        back_to_back = self._find_back_to_back(events)
        if len(back_to_back) >= 3:
            insights.append(
                Insight(
                    id=f"cal_b2b_{now.isoformat()}",
                    category=InsightCategory.CALENDAR,
                    priority=InsightPriority.MEDIUM,
                    title="Heavy Meeting Day",
                    message=f"You have {len(back_to_back)} back-to-back meetings. Consider adding breaks.",
                    icon="warning",
                    source="calendar",
                    data={"count": len(back_to_back)},
                    actions=[
                        {
                            "text": "Add breaks",
                            "action": "message",
                            "payload": "Help me add breaks between my meetings",
                        },
                    ],
                )
            )

        # Check for location changes (for hybrid workers)
        if historical_events:
            location_changes = self._detect_location_changes(events, historical_events)
            for change in location_changes:
                insights.append(
                    Insight(
                        id=f"cal_loc_{change['event_id']}",
                        category=InsightCategory.CALENDAR,
                        priority=InsightPriority.HIGH,
                        title="Meeting Location Changed",
                        message=f"'{change['title']}' location changed to {change['new_location']}",
                        icon="location",
                        source="calendar",
                        data=change,
                    )
                )

        return insights

    def _is_within_hours(self, time_str: Optional[str], hours: int) -> bool:
        """Check if a time is within the next N hours."""
        if not time_str:
            return False
        try:
            event_time = self._parse_time(time_str)
            if event_time:
                now = datetime.now(timezone.utc)
                return now <= event_time <= now + timedelta(hours=hours)
        except Exception:
            pass
        return False

    def _minutes_until(self, time_str: Optional[str]) -> Optional[int]:
        """Get minutes until a time."""
        if not time_str:
            return None
        try:
            event_time = self._parse_time(time_str)
            if event_time:
                delta = event_time - datetime.now(timezone.utc)
                return int(delta.total_seconds() / 60)
        except Exception:
            pass
        return None

    def _parse_time(self, time_str: Optional[str]) -> Optional[datetime]:
        """Parse a time string."""
        if not time_str:
            return None
        try:
            if isinstance(time_str, datetime):
                return time_str
            return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        except Exception:
            return None

    def _find_schedule_gaps(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find gaps in the schedule."""
        gaps = []
        sorted_events = sorted([e for e in events if e.get("start") and e.get("end")], key=lambda e: e["start"])

        now = datetime.now(timezone.utc)

        for i in range(len(sorted_events) - 1):
            current_end = self._parse_time(sorted_events[i]["end"])
            next_start = self._parse_time(sorted_events[i + 1]["start"])

            if current_end and next_start and current_end < next_start:
                gap_minutes = int((next_start - current_end).total_seconds() / 60)
                if gap_minutes >= 30:  # At least 30 minutes
                    gaps.append(
                        {
                            "start": current_end,
                            "end": next_start,
                            "duration": gap_minutes,
                        }
                    )

        return [g for g in gaps if g["start"] >= now]

    def _find_back_to_back(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find back-to-back meetings."""
        back_to_back = []
        sorted_events = sorted([e for e in events if e.get("start") and e.get("end")], key=lambda e: e["start"])

        for i in range(len(sorted_events) - 1):
            current_end = self._parse_time(sorted_events[i]["end"])
            next_start = self._parse_time(sorted_events[i + 1]["start"])

            if current_end and next_start:
                gap = (next_start - current_end).total_seconds() / 60
                if gap <= 5:  # 5 minutes or less between meetings
                    if sorted_events[i] not in back_to_back:
                        back_to_back.append(sorted_events[i])
                    back_to_back.append(sorted_events[i + 1])

        return back_to_back

    def _detect_location_changes(
        self, current: List[Dict[str, Any]], historical: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect meetings where the location has changed."""
        changes = []

        current_map = {e.get("id"): e for e in current if e.get("id")}
        historical_map = {e.get("id"): e for e in historical if e.get("id")}

        for event_id, event in current_map.items():
            if event_id in historical_map:
                old_loc = historical_map[event_id].get("location", "")
                new_loc = event.get("location", "")
                if old_loc and new_loc and old_loc != new_loc:
                    changes.append(
                        {
                            "event_id": event_id,
                            "title": event.get("title", ""),
                            "old_location": old_loc,
                            "new_location": new_loc,
                        }
                    )

        return changes


class WeatherInsightGenerator:
    """Generates insights from weather data."""

    async def generate(
        self,
        current_weather: Optional[Dict[str, Any]],
        forecast: Optional[List[Dict[str, Any]]],
        calendar_events: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Insight]:
        """Generate weather-related insights."""
        insights = []
        now = datetime.now(timezone.utc)

        # Check for significant weather alerts
        if current_weather:
            conditions = current_weather.get("description", "").lower()
            temp = current_weather.get("temperature", 0)

            # Extreme temperature alerts
            if temp >= 35:
                insights.append(
                    Insight(
                        id=f"weather_hot_{now.isoformat()}",
                        category=InsightCategory.WEATHER,
                        priority=InsightPriority.HIGH,
                        title="Extreme Heat Warning",
                        message=f"It's {temp}C outside. Stay hydrated and avoid prolonged sun exposure.",
                        icon="hot",
                        source="weather",
                        data={"temperature": temp},
                        expires_at=now + timedelta(hours=4),
                    )
                )
            elif temp <= 0:
                insights.append(
                    Insight(
                        id=f"weather_cold_{now.isoformat()}",
                        category=InsightCategory.WEATHER,
                        priority=InsightPriority.MEDIUM,
                        title="Cold Weather Alert",
                        message=f"It's {temp}C outside. Bundle up if going out!",
                        icon="cold",
                        source="weather",
                        data={"temperature": temp},
                        expires_at=now + timedelta(hours=4),
                    )
                )

            # Precipitation alerts
            if any(w in conditions for w in ["rain", "storm", "thunder"]):
                insights.append(
                    Insight(
                        id=f"weather_rain_{now.isoformat()}",
                        category=InsightCategory.WEATHER,
                        priority=InsightPriority.MEDIUM,
                        title="Rain Alert",
                        message=f"Current conditions: {conditions}. Don't forget an umbrella!",
                        icon="rain",
                        source="weather",
                        data={"conditions": conditions},
                        expires_at=now + timedelta(hours=2),
                    )
                )

        # Check forecast against outdoor events
        if forecast and calendar_events:
            outdoor_keywords = ["outdoor", "outside", "park", "walk", "run", "hike", "picnic", "bbq", "golf", "tennis"]

            for event in calendar_events:
                event_title = event.get("title", "").lower()
                event_location = event.get("location", "").lower()
                combined = f"{event_title} {event_location}"

                if any(k in combined for k in outdoor_keywords):
                    event_date = self._parse_date(event.get("start"))
                    if event_date:
                        # Find forecast for that day
                        for day_forecast in forecast:
                            forecast_date = self._parse_date(day_forecast.get("date"))
                            if forecast_date and forecast_date.date() == event_date.date():
                                conditions = day_forecast.get("conditions", "").lower()
                                if any(w in conditions for w in ["rain", "storm", "thunder"]):
                                    insights.append(
                                        Insight(
                                            id=f"weather_event_{event.get('id', '')}",
                                            category=InsightCategory.WEATHER,
                                            priority=InsightPriority.HIGH,
                                            title="Weather Alert for Your Event",
                                            message=f"Rain expected during '{event.get('title')}' on {event_date.strftime('%A')}",
                                            icon="warning",
                                            source="weather",
                                            data={
                                                "event": event,
                                                "forecast": day_forecast,
                                            },
                                            actions=[
                                                {
                                                    "text": "Find indoor alternatives",
                                                    "action": "message",
                                                    "payload": f"What indoor alternatives are there for {event.get('title')}?",
                                                },
                                                {
                                                    "text": "Reschedule",
                                                    "action": "message",
                                                    "payload": f"When's a better day for outdoor activities this week?",
                                                },
                                            ],
                                            expires_at=event_date,
                                        )
                                    )
                                break

        return insights

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse a date string."""
        if not date_str:
            return None
        try:
            if isinstance(date_str, datetime):
                return date_str
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return None


class EmailInsightGenerator:
    """Generates insights from email data."""

    def __init__(self, important_senders: Optional[Set[str]] = None):
        """Initialize with optional set of important senders."""
        self.important_senders = important_senders or set()

    async def generate(self, recent_emails: List[Dict[str, Any]], unread_count: int = 0) -> List[Insight]:
        """Generate email-related insights."""
        insights = []
        now = datetime.now(timezone.utc)

        # Group emails by sender
        sender_counts: Dict[str, int] = {}
        for email in recent_emails:
            sender = email.get("sender", "Unknown")
            if not email.get("is_read", True):
                sender_counts[sender] = sender_counts.get(sender, 0) + 1

        # Alert for emails from important senders
        for sender, count in sender_counts.items():
            sender_lower = sender.lower()
            is_important = (
                any(imp.lower() in sender_lower for imp in self.important_senders) if self.important_senders else False
            )

            # Also check for common important patterns
            if any(p in sender_lower for p in ["manager", "director", "ceo", "cto", "hr", "urgent"]):
                is_important = True

            if is_important and count > 0:
                insights.append(
                    Insight(
                        id=f"email_important_{sender}",
                        category=InsightCategory.EMAIL,
                        priority=InsightPriority.HIGH,
                        title="Important Unread Emails",
                        message=f"You have {count} unread email{'s' if count > 1 else ''} from {sender}",
                        icon="mail",
                        source="email",
                        data={"sender": sender, "count": count},
                        actions=[
                            {"text": "Show emails", "action": "message", "payload": f"Show me emails from {sender}"},
                        ],
                    )
                )

        # Overall unread alert
        if unread_count > 10:
            priority = InsightPriority.MEDIUM if unread_count < 25 else InsightPriority.HIGH
            insights.append(
                Insight(
                    id=f"email_unread_{now.isoformat()}",
                    category=InsightCategory.EMAIL,
                    priority=priority,
                    title="Inbox Needs Attention",
                    message=f"You have {unread_count} unread emails",
                    icon="mailbox",
                    source="email",
                    data={"unread_count": unread_count},
                    actions=[
                        {"text": "Summarize inbox", "action": "message", "payload": "Give me an inbox summary"},
                        {
                            "text": "Show important",
                            "action": "message",
                            "payload": "Show me the most important unread emails",
                        },
                    ],
                )
            )

        # Check for thread activity (same subject multiple times)
        subject_counts: Dict[str, List[Dict]] = {}
        for email in recent_emails:
            subject = email.get("subject", "").strip()
            if subject:
                # Normalize subject (remove Re:, Fwd:, etc.)
                clean_subject = subject
                for prefix in ["re:", "fwd:", "fw:", "re[", "fwd["]:
                    while clean_subject.lower().startswith(prefix):
                        clean_subject = clean_subject[len(prefix) :].strip()

                if clean_subject not in subject_counts:
                    subject_counts[clean_subject] = []
                subject_counts[clean_subject].append(email)

        for subject, emails in subject_counts.items():
            if len(emails) >= 3:
                insights.append(
                    Insight(
                        id=f"email_thread_{hash(subject)}",
                        category=InsightCategory.EMAIL,
                        priority=InsightPriority.MEDIUM,
                        title="Active Email Thread",
                        message=f"'{subject[:50]}...' has {len(emails)} recent messages",
                        icon="chat",
                        source="email",
                        data={"subject": subject, "count": len(emails)},
                        actions=[
                            {
                                "text": "View thread",
                                "action": "message",
                                "payload": f"Show me emails about {subject[:30]}",
                            },
                        ],
                    )
                )

        return insights


# ============================================================================
# Main Insight Engine
# ============================================================================


class InsightEngine:
    """
    Main engine for generating proactive insights.

    Combines multiple insight generators and manages:
    - Insight generation from various data sources
    - Morning briefings
    - Insight prioritization and deduplication
    - Insight expiration
    """

    def __init__(
        self,
        important_senders: Optional[Set[str]] = None,
    ):
        """Initialize the insight engine."""
        self.calendar_generator = CalendarInsightGenerator()
        self.weather_generator = WeatherInsightGenerator()
        self.email_generator = EmailInsightGenerator(important_senders)
        self._cached_insights: List[Insight] = []
        self._last_generated: Optional[datetime] = None

    async def generate_insights(
        self,
        calendar_events: Optional[List[Dict[str, Any]]] = None,
        current_weather: Optional[Dict[str, Any]] = None,
        weather_forecast: Optional[List[Dict[str, Any]]] = None,
        recent_emails: Optional[List[Dict[str, Any]]] = None,
        unread_email_count: int = 0,
    ) -> List[Insight]:
        """
        Generate insights from all available data sources.

        Args:
            calendar_events: Today's calendar events
            current_weather: Current weather conditions
            weather_forecast: Weather forecast for coming days
            recent_emails: Recent email messages
            unread_email_count: Total unread email count

        Returns:
            List of insights sorted by priority
        """
        all_insights: List[Insight] = []

        # Generate calendar insights
        if calendar_events:
            calendar_insights = await self.calendar_generator.generate(calendar_events)
            all_insights.extend(calendar_insights)

        # Generate weather insights
        if current_weather or weather_forecast:
            weather_insights = await self.weather_generator.generate(
                current_weather, weather_forecast, calendar_events
            )
            all_insights.extend(weather_insights)

        # Generate email insights
        if recent_emails:
            email_insights = await self.email_generator.generate(recent_emails, unread_email_count)
            all_insights.extend(email_insights)

        # Remove expired insights
        now = datetime.now(timezone.utc)
        valid_insights = [i for i in all_insights if not i.expires_at or i.expires_at > now]

        # Deduplicate by ID
        seen_ids: Set[str] = set()
        unique_insights = []
        for insight in valid_insights:
            if insight.id not in seen_ids:
                seen_ids.add(insight.id)
                unique_insights.append(insight)

        # Sort by priority
        priority_order = {
            InsightPriority.CRITICAL: 0,
            InsightPriority.HIGH: 1,
            InsightPriority.MEDIUM: 2,
            InsightPriority.LOW: 3,
        }
        sorted_insights = sorted(unique_insights, key=lambda i: priority_order.get(i.priority, 99))

        self._cached_insights = sorted_insights
        self._last_generated = now

        return sorted_insights

    async def generate_morning_briefing(
        self,
        user_name: Optional[str] = None,
        calendar_events: Optional[List[Dict[str, Any]]] = None,
        current_weather: Optional[Dict[str, Any]] = None,
        weather_forecast: Optional[List[Dict[str, Any]]] = None,
        recent_emails: Optional[List[Dict[str, Any]]] = None,
        unread_email_count: int = 0,
        priorities: Optional[List[Dict[str, Any]]] = None,
    ) -> MorningBriefing:
        """
        Generate a comprehensive morning briefing.

        This combines all data sources into a cohesive summary.
        """
        now = datetime.now()

        # Personalized greeting
        hour = now.hour
        if hour < 12:
            time_greeting = "Good morning"
        elif hour < 17:
            time_greeting = "Good afternoon"
        else:
            time_greeting = "Good evening"

        greeting = f"{time_greeting}"
        if user_name:
            greeting += f", {user_name}"
        greeting += "!"

        # Date summary
        date_summary = now.strftime("%A, %B %d")

        # Weather summary
        weather_summary = None
        if current_weather:
            temp = current_weather.get("temperature", "")
            desc = current_weather.get("description", "")
            if temp and desc:
                weather_summary = f"It's {temp}C and {desc.lower()} outside"

        # Calendar summary
        if calendar_events:
            event_count = len(calendar_events)
            if event_count == 0:
                calendar_summary = "Your calendar is clear today - great day for deep work!"
            elif event_count == 1:
                first_event = calendar_events[0]
                calendar_summary = f"You have 1 event today: {first_event.get('title', 'Meeting')}"
            else:
                first_event = calendar_events[0]
                calendar_summary = f"You have {event_count} events today, starting with {first_event.get('title', 'your first meeting')}"
        else:
            calendar_summary = "No calendar data available"

        # Priority summary
        if priorities:
            top_priorities = priorities[:3]
            priority_items = [p.get("title", p.get("subject", "Item")) for p in top_priorities]
            priority_summary = f"Top priorities: {', '.join(priority_items)}"
        else:
            priority_summary = "Check your inbox for priorities"

        # Email summary
        email_summary = None
        if unread_email_count > 0:
            email_summary = f"You have {unread_email_count} unread emails"

        # Generate insights
        insights = await self.generate_insights(
            calendar_events=calendar_events,
            current_weather=current_weather,
            weather_forecast=weather_forecast,
            recent_emails=recent_emails,
            unread_email_count=unread_email_count,
        )

        # Only include high-priority insights in briefing
        briefing_insights = [i for i in insights if i.priority in [InsightPriority.CRITICAL, InsightPriority.HIGH]][
            :3
        ]  # Max 3 insights

        # Suggested focus
        if calendar_events and len(calendar_events) >= 4:
            suggested_focus = "You have a busy day ahead. Consider tackling your top priority early."
        elif not calendar_events or len(calendar_events) == 0:
            suggested_focus = "With a clear calendar, it's a great day for focused deep work."
        elif priorities:
            top = priorities[0].get("title", priorities[0].get("subject", "your top priority"))
            suggested_focus = f"Consider focusing on: {top}"
        else:
            suggested_focus = "Take some time to review your inbox and plan your day."

        return MorningBriefing(
            greeting=greeting,
            date_summary=date_summary,
            weather_summary=weather_summary,
            calendar_summary=calendar_summary,
            priority_summary=priority_summary,
            email_summary=email_summary,
            insights=briefing_insights,
            suggested_focus=suggested_focus,
        )

    def get_cached_insights(self) -> List[Insight]:
        """Get cached insights without regenerating."""
        now = datetime.now(timezone.utc)

        # Filter out expired insights
        valid = [i for i in self._cached_insights if not i.expires_at or i.expires_at > now]

        return valid

    def dismiss_insight(self, insight_id: str) -> bool:
        """Mark an insight as dismissed."""
        for insight in self._cached_insights:
            if insight.id == insight_id:
                insight.dismissed = True
                return True
        return False


# ============================================================================
# Factory Functions
# ============================================================================


def create_insight_engine(important_senders: Optional[Set[str]] = None) -> InsightEngine:
    """Create an insight engine instance."""
    return InsightEngine(important_senders=important_senders)


# ============================================================================
# Singleton Instance
# ============================================================================

_insight_engine: Optional[InsightEngine] = None


def get_insight_engine() -> InsightEngine:
    """Get or create the singleton insight engine."""
    global _insight_engine
    if _insight_engine is None:
        _insight_engine = InsightEngine()
    return _insight_engine
