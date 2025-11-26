"""
Tools module for the conversational agent.

This module provides LangChain-compatible tools that the agent can use
to perform various actions like planning, weather queries, calendar management,
email search, and knowledge retrieval.

Each tool is defined using the @tool decorator pattern and returns
structured output using Pydantic models for reliability.
"""

from orchestrator.tools.planning import (
    plan_day,
    get_priority_items,
    PlanDayOutput,
)
from orchestrator.tools.weather import (
    get_current_weather,
    get_weather_forecast,
    WeatherOutput,
    ForecastOutput,
)
from orchestrator.tools.calendar import (
    get_todays_events,
    get_upcoming_events,
    create_calendar_event,
    CalendarEventOutput,
)
from orchestrator.tools.inbox import (
    search_emails,
    get_recent_emails,
    get_email_summary,
    EmailSearchOutput,
)
from orchestrator.tools.rag import (
    query_knowledge_base,
    RAGQueryOutput,
)
from orchestrator.tools.actions import (
    get_pending_actions,
    PendingActionsOutput,
)
from orchestrator.tools.cross_domain import (
    find_related_items,
    get_person_context,
    prepare_for_meeting,
    CROSS_DOMAIN_TOOLS,
)

# All available tools for the conversational agent
ALL_TOOLS = [
    plan_day,
    get_priority_items,
    get_current_weather,
    get_weather_forecast,
    get_todays_events,
    get_upcoming_events,
    create_calendar_event,
    search_emails,
    get_recent_emails,
    get_email_summary,
    query_knowledge_base,
    get_pending_actions,
    find_related_items,
    get_person_context,
    prepare_for_meeting,
]

# Categorized tools
PLANNING_TOOLS = [plan_day, get_priority_items]
WEATHER_TOOLS = [get_current_weather, get_weather_forecast]
CALENDAR_TOOLS = [get_todays_events, get_upcoming_events, create_calendar_event]
INBOX_TOOLS = [search_emails, get_recent_emails, get_email_summary]
KNOWLEDGE_TOOLS = [query_knowledge_base]
ACTION_TOOLS = [get_pending_actions]
CROSS_DOMAIN_TOOLS_LIST = CROSS_DOMAIN_TOOLS

__all__ = [
    # Planning
    "plan_day",
    "get_priority_items",
    "PlanDayOutput",
    # Weather
    "get_current_weather",
    "get_weather_forecast",
    "WeatherOutput",
    "ForecastOutput",
    # Calendar
    "get_todays_events",
    "get_upcoming_events",
    "create_calendar_event",
    "CalendarEventOutput",
    # Inbox
    "search_emails",
    "get_recent_emails",
    "get_email_summary",
    "EmailSearchOutput",
    # RAG
    "query_knowledge_base",
    "RAGQueryOutput",
    # Actions
    "get_pending_actions",
    "PendingActionsOutput",
    # Cross-domain intelligence
    "find_related_items",
    "get_person_context",
    "prepare_for_meeting",
    # Collections
    "ALL_TOOLS",
    "PLANNING_TOOLS",
    "WEATHER_TOOLS",
    "CALENDAR_TOOLS",
    "INBOX_TOOLS",
    "KNOWLEDGE_TOOLS",
    "ACTION_TOOLS",
    "CROSS_DOMAIN_TOOLS_LIST",
]
