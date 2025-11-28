"""
Tool UI Mapping - Maps tools to their UI representation.

Each tool declares:
- page: Which page to navigate to
- cursor: CSS selector for cursor target
- thought: Reasoning message template
- safe: Whether action is safe to auto-execute
- reversible: Whether action can be undone
- preview_type: Type of preview to show (if any)
"""

from typing import Any, Dict, Optional


# =============================================================================
# Tool UI Configuration
# =============================================================================

TOOL_UI_CONFIG: Dict[str, Dict[str, Any]] = {
    # -------------------------------------------------------------------------
    # Weather Tools - All safe (read-only)
    # -------------------------------------------------------------------------
    "get_current_weather": {
        "page": "/weather",
        "cursor": "[data-weather-current]",
        "thought": "Checking current weather conditions...",
        "safe": True,
        "reversible": True,
    },
    "get_weather_forecast": {
        "page": "/weather",
        "cursor": "[data-weather-forecast]",
        "thought": "Getting weather forecast...",
        "safe": True,
        "reversible": True,
    },
    # -------------------------------------------------------------------------
    # Calendar Tools
    # -------------------------------------------------------------------------
    "get_todays_events": {
        "page": "/calendar",
        "cursor": "[data-today-column]",
        "thought": "Checking today's calendar...",
        "safe": True,
        "reversible": True,
    },
    "get_upcoming_events": {
        "page": "/calendar",
        "cursor": "[data-calendar-grid]",
        "thought": "Looking at upcoming events...",
        "safe": True,
        "reversible": True,
    },
    "create_calendar_event": {
        "page": "/calendar",
        "cursor": "[data-time-slot='{start_time}']",
        "thought": "Creating event: {title}...",
        "safe": False,  # Creates data
        "reversible": True,  # Can delete event
        "preview_type": "calendar_event",
    },
    # -------------------------------------------------------------------------
    # Email/Inbox Tools
    # -------------------------------------------------------------------------
    "search_emails": {
        "page": "/inbox",
        "cursor": "[data-email-search]",
        "thought": "Searching emails for '{query}'...",
        "safe": True,
        "reversible": True,
    },
    "get_recent_emails": {
        "page": "/inbox",
        "cursor": "[data-email-list]",
        "thought": "Getting recent emails...",
        "safe": True,
        "reversible": True,
    },
    "get_email_summary": {
        "page": "/inbox",
        "cursor": "[data-inbox-summary]",
        "thought": "Summarizing your inbox...",
        "safe": True,
        "reversible": True,
    },
    "create_email_draft": {
        "page": "/inbox",
        "cursor": "[data-compose-area]",
        "thought": "Drafting email to {to}...",
        "safe": True,  # Drafts are safe (not sent)
        "reversible": True,
        "preview_type": "email_draft",
    },
    "send_email": {
        "page": "/inbox",
        "cursor": "[data-send-button]",
        "thought": "Sending email...",
        "safe": False,  # Irreversible
        "reversible": False,
        "preview_type": "email_send",
    },
    # -------------------------------------------------------------------------
    # Planning Tools - Safe (read/analyze)
    # -------------------------------------------------------------------------
    "plan_day": {
        "page": "/",
        "cursor": "[data-dashboard-plan]",
        "thought": "Creating your daily plan...",
        "safe": True,
        "reversible": True,
    },
    "get_priority_items": {
        "page": "/",
        "cursor": "[data-priorities]",
        "thought": "Analyzing your priorities...",
        "safe": True,
        "reversible": True,
    },
    # -------------------------------------------------------------------------
    # Knowledge/RAG Tools - Safe (read-only)
    # -------------------------------------------------------------------------
    "query_knowledge_base": {
        "page": None,  # No specific page
        "cursor": None,
        "thought": "Searching knowledge base...",
        "safe": True,
        "reversible": True,
    },
    # -------------------------------------------------------------------------
    # Action Tools
    # -------------------------------------------------------------------------
    "get_pending_actions": {
        "page": "/",
        "cursor": "[data-pending-actions]",
        "thought": "Checking pending actions...",
        "safe": True,
        "reversible": True,
    },
    # -------------------------------------------------------------------------
    # Cross-Domain Tools - Safe (read/analyze)
    # -------------------------------------------------------------------------
    "find_related_items": {
        "page": None,
        "cursor": None,
        "thought": "Finding related items...",
        "safe": True,
        "reversible": True,
    },
    "get_person_context": {
        "page": None,
        "cursor": None,
        "thought": "Getting context about {person}...",
        "safe": True,
        "reversible": True,
    },
    "prepare_for_meeting": {
        "page": "/calendar",
        "cursor": "[data-meeting-prep]",
        "thought": "Preparing for your meeting...",
        "safe": True,
        "reversible": True,
    },
    # -------------------------------------------------------------------------
    # Settings Tools - Categorized by safety
    # -------------------------------------------------------------------------
    "set_user_location": {
        "page": "/weather",
        "cursor": "[data-location-badge]",
        "thought": "Updating your location to {city}...",
        "safe": True,  # Display preference
        "reversible": True,
        "preview_type": "setting_change",
    },
    "set_temperature_unit": {
        "page": "/weather",
        "cursor": "[data-temp-unit]",
        "thought": "Changing temperature unit to {unit}...",
        "safe": True,  # Display preference
        "reversible": True,
    },
    "set_time_format": {
        "page": "/settings",
        "cursor": "[data-time-format]",
        "thought": "Updating time format...",
        "safe": True,
        "reversible": True,
    },
    "set_theme": {
        "page": "/settings",
        "cursor": "[data-theme-toggle]",
        "thought": "Changing theme...",
        "safe": True,
        "reversible": True,
    },
}


# =============================================================================
# Settings Safety Classification
# =============================================================================

SAFE_SETTINGS = {
    "temp_unit",
    "location",
    "location_city",
    "location_country",
    "time_format",
    "date_format",
    "week_starts_on",
    "theme",
    "response_style",
    "agent_cursor",
    "thought_bubbles",
    "confetti_enabled",
    "agent_speed",
    "reduced_motion",
    "timezone",
}

SENSITIVE_SETTINGS = {
    "auto_approve_all",
    "auto_approve_low_risk",
    "learn_preferences",
    "max_auto_actions",
    "data_retention",
    "save_chat_history",
    "enable_memory",
    "persist_memory",
    "share_memory_across_chats",
}


# =============================================================================
# Helper Functions
# =============================================================================


def get_tool_ui(tool_name: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get UI configuration for a tool with args interpolated into templates.

    Args:
        tool_name: Name of the tool
        args: Arguments passed to the tool (for template interpolation)

    Returns:
        UI configuration dict with page, cursor, thought, safe, etc.
    """
    config = TOOL_UI_CONFIG.get(tool_name, {}).copy()
    args = args or {}

    # Interpolate thought template
    if config.get("thought"):
        try:
            config["thought"] = config["thought"].format(**args)
        except KeyError:
            pass  # Keep original if args don't match

    # Interpolate cursor template
    if config.get("cursor"):
        try:
            config["cursor"] = config["cursor"].format(**args)
        except KeyError:
            pass

    return config


def is_tool_safe(tool_name: str) -> bool:
    """Check if a tool is safe to auto-execute without approval."""
    config = TOOL_UI_CONFIG.get(tool_name, {})
    return config.get("safe", False)


def is_tool_reversible(tool_name: str) -> bool:
    """Check if a tool's action can be undone."""
    config = TOOL_UI_CONFIG.get(tool_name, {})
    return config.get("reversible", True)


def get_tool_page(tool_name: str) -> Optional[str]:
    """Get the page a tool should navigate to."""
    config = TOOL_UI_CONFIG.get(tool_name, {})
    return config.get("page")


def get_tool_preview_type(tool_name: str) -> Optional[str]:
    """Get the preview type for a tool (if any)."""
    config = TOOL_UI_CONFIG.get(tool_name, {})
    return config.get("preview_type")


def is_setting_safe(setting_key: str) -> bool:
    """Check if a setting is safe to change without approval."""
    return setting_key in SAFE_SETTINGS


def is_setting_sensitive(setting_key: str) -> bool:
    """Check if a setting requires approval to change."""
    return setting_key in SENSITIVE_SETTINGS


# =============================================================================
# Preview Types
# =============================================================================

PREVIEW_TYPES = {
    "calendar_event": {
        "component": "CalendarEventPreview",
        "style": "ghost",  # Dashed border, 50% opacity
    },
    "email_draft": {
        "component": "EmailDraftPreview",
        "style": "ghost",
    },
    "email_send": {
        "component": "EmailSendPreview",
        "style": "warning",  # Amber border
    },
    "setting_change": {
        "component": "SettingChangePreview",
        "style": "info",
    },
}


def get_preview_config(preview_type: str) -> Dict[str, Any]:
    """Get configuration for a preview type."""
    return PREVIEW_TYPES.get(preview_type, {})
