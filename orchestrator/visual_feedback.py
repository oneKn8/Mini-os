"""
Visual Feedback Coordinator for Agent Actions

Maps agent actions to UI element highlights and ghost previews.
Provides Cursor-style real-time visual feedback.
"""

import logging
import uuid
from typing import Any, Dict, Optional
from orchestrator.streaming import AgentStreamingSession

logger = logging.getLogger(__name__)


# Tool-to-selector mapping
TOOL_SELECTORS = {
    "search_emails": "[data-component='email-list']",
    "get_recent_emails": "[data-component='email-list']",
    "get_email_summary": "[data-component='inbox-summary']",
    "create_email_draft": "[data-component='email-composer']",
    "get_todays_events": "[data-component='calendar-view']",
    "get_upcoming_events": "[data-component='calendar-view']",
    "create_calendar_event": "[data-component='calendar-view']",
    "get_current_weather": "[data-component='weather-widget']",
    "get_weather_forecast": "[data-component='weather-widget']",
    "get_priority_items": "[data-component='priority-list']",
    "get_pending_actions": "[data-component='action-list']",
    "plan_day": "[data-component='daily-plan']",
    "find_related_items": "[data-component='sidebar']",
    "get_person_context": "[data-component='person-card']",
    "prepare_for_meeting": "[data-component='meeting-brief']",
    "query_knowledge_base": "[data-component='search-results']",
}


# Tool-to-message mapping
TOOL_MESSAGES = {
    "search_emails": "Searching your emails",
    "get_recent_emails": "Getting recent emails",
    "get_email_summary": "Analyzing your inbox",
    "create_email_draft": "Drafting email",
    "get_todays_events": "Checking your calendar",
    "get_upcoming_events": "Looking at upcoming events",
    "create_calendar_event": "Creating calendar event",
    "get_current_weather": "Checking weather",
    "get_weather_forecast": "Getting forecast",
    "get_priority_items": "Finding priorities",
    "get_pending_actions": "Checking pending actions",
    "plan_day": "Planning your day",
    "find_related_items": "Finding connections",
    "get_person_context": "Getting context",
    "prepare_for_meeting": "Preparing meeting brief",
    "query_knowledge_base": "Searching knowledge",
}


class VisualFeedbackCoordinator:
    """
    Coordinates visual feedback for agent actions.

    Emits:
    - Element highlights when tools execute
    - Ghost previews for create operations
    - Completion animations
    """

    def __init__(self, streaming_session: Optional[AgentStreamingSession] = None):
        """
        Initialize visual feedback coordinator.

        Args:
            streaming_session: Streaming session for emitting events
        """
        self.streaming = streaming_session
        self.active_highlights: Dict[str, str] = {}  # selector -> state
        self.active_previews: Dict[str, Dict] = {}  # preview_id -> data

    async def start_tool_execution(self, tool_name: str, args: Dict[str, Any]) -> None:
        """
        Emit visual feedback when tool starts.

        Args:
            tool_name: Name of tool starting
            args: Tool arguments
        """
        if not self.streaming:
            return

        # Get selector for this tool
        selector = TOOL_SELECTORS.get(tool_name)
        if not selector:
            logger.debug(f"No selector mapped for tool: {tool_name}")
            return

        # Get message
        message = TOOL_MESSAGES.get(tool_name, f"Running {tool_name}")

        # Emit thinking state
        await self.streaming.emit_highlight(
            selector=selector,
            state="thinking",
            message=message,
            duration_ms=3000,
        )

        self.active_highlights[tool_name] = selector

    async def update_tool_progress(
        self,
        tool_name: str,
        progress_percent: int,
        message: str = "",
    ) -> None:
        """
        Update visual feedback during tool execution.

        Args:
            tool_name: Name of tool
            progress_percent: Progress percentage (0-100)
            message: Optional progress message
        """
        if not self.streaming:
            return

        selector = self.active_highlights.get(tool_name) or TOOL_SELECTORS.get(tool_name)
        if not selector:
            return

        # Emit working state
        await self.streaming.emit_highlight(
            selector=selector,
            state="working",
            message=message or f"{progress_percent}% complete",
            duration_ms=1000,
        )

    async def complete_tool_execution(
        self,
        tool_name: str,
        result: Any,
        success: bool = True,
    ) -> None:
        """
        Emit visual feedback when tool completes.

        Args:
            tool_name: Name of tool
            result: Tool result
            success: Whether tool succeeded
        """
        if not self.streaming:
            return

        selector = self.active_highlights.get(tool_name) or TOOL_SELECTORS.get(tool_name)
        if not selector:
            return

        # Emit completion state
        state = "done" if success else "error"
        await self.streaming.emit_highlight(
            selector=selector,
            state=state,
            message="Complete" if success else "Failed",
            duration_ms=2000,
        )

        # Emit checkmark animation for success
        if success:
            await self.streaming.emit_animation(
                animation_type="checkmark",
                target_selector=selector,
                duration_ms=500,
            )

        # Clean up
        self.active_highlights.pop(tool_name, None)

    async def show_ghost_preview(
        self,
        component_type: str,
        data: Dict[str, Any],
        action: str = "create",
        requires_confirmation: bool = True,
    ) -> str:
        """
        Show ghost preview of upcoming change.

        Args:
            component_type: Type of component (email, event, task)
            data: Preview data
            action: Action type (create, update, delete)
            requires_confirmation: Whether user must confirm

        Returns:
            Preview ID for later reference
        """
        if not self.streaming:
            return ""

        preview_id = str(uuid.uuid4())

        await self.streaming.emit_ghost_preview(
            component_type=component_type,
            data=data,
            action=action,
            preview_id=preview_id,
            requires_confirmation=requires_confirmation,
        )

        # Track active preview
        self.active_previews[preview_id] = {
            "component_type": component_type,
            "data": data,
            "action": action,
        }

        return preview_id

    async def dismiss_ghost_preview(self, preview_id: str) -> None:
        """
        Dismiss a ghost preview.

        Args:
            preview_id: ID of preview to dismiss
        """
        if not self.streaming:
            return

        # Emit dismiss event (just a special animation)
        await self.streaming.emit_animation(
            animation_type="fade_out",
            target_selector=f"[data-preview-id='{preview_id}']",
            duration_ms=300,
        )

        # Clean up
        self.active_previews.pop(preview_id, None)

    async def highlight_query_result(
        self,
        selector: str,
        message: str,
        duration_ms: int = 3000,
    ) -> None:
        """
        Highlight a query result in the UI.

        Args:
            selector: CSS selector
            message: Message to show
            duration_ms: Duration to show highlight
        """
        if not self.streaming:
            return

        await self.streaming.emit_highlight(
            selector=selector,
            state="done",
            message=message,
            duration_ms=duration_ms,
            color="#10b981",  # Green
        )

    def clear_all_highlights(self) -> None:
        """Clear all active highlights."""
        self.active_highlights.clear()

    def clear_all_previews(self) -> None:
        """Clear all active previews."""
        self.active_previews.clear()

    def get_active_highlights(self) -> Dict[str, str]:
        """Get all active highlights."""
        return self.active_highlights.copy()

    def get_active_previews(self) -> Dict[str, Dict]:
        """Get all active previews."""
        return self.active_previews.copy()
