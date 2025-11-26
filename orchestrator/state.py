"""
LangGraph state model for multi-agent orchestration.
Based on the pattern from GenerativeAIExamples smart-health-agent.

Enhanced with:
- Conversation history for context-aware responses
- Current datetime for time-aware reasoning
- User context (location, timezone, preferences)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MessageEntry(BaseModel):
    """A single message in the conversation history."""

    role: str = Field(description="Message role: user, assistant, or system")
    content: str = Field(description="Message content")
    timestamp: Optional[str] = Field(default=None, description="ISO timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UserContext(BaseModel):
    """User context for personalization."""

    user_id: str = Field(default="default")
    timezone: str = Field(default="UTC")
    location: Dict[str, str] = Field(default_factory=dict, description="User's location: {city, country}")
    preferences: Dict[str, Any] = Field(
        default_factory=dict, description="User preferences like email_tone, quiet_hours, etc."
    )

    @classmethod
    def from_db_user(cls, user) -> "UserContext":
        """Create UserContext from a database User model."""
        if user is None:
            return cls()

        location = {}
        if hasattr(user, "location_city") and user.location_city:
            location["city"] = user.location_city
        if hasattr(user, "location_country") and user.location_country:
            location["country"] = user.location_country

        preferences = {}
        if hasattr(user, "preferences") and user.preferences:
            prefs = user.preferences
            if hasattr(prefs, "email_tone"):
                preferences["email_tone"] = prefs.email_tone
            if hasattr(prefs, "quiet_hours_start"):
                preferences["quiet_hours_start"] = prefs.quiet_hours_start
            if hasattr(prefs, "quiet_hours_end"):
                preferences["quiet_hours_end"] = prefs.quiet_hours_end

        return cls(
            user_id=str(user.id) if hasattr(user, "id") else "default",
            timezone=user.timezone if hasattr(user, "timezone") and user.timezone else "UTC",
            location=location,
            preferences=preferences,
        )


class OpsAgentState(BaseModel):
    """
    State passed through LangGraph workflow for multi-agent orchestration.

    This state model carries all context needed for agents to:
    - Understand the user's request
    - Access conversation history
    - Know current time and user context
    - Track action proposals and results
    """

    # Core identifiers
    user_id: str = Field(description="User identifier")
    intent: str = Field(default="conversation", description="Intent: conversation, plan_day, refresh_inbox, etc.")

    # Conversation context
    conversation_history: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of previous messages: [{role, content, timestamp}]"
    )
    current_message: str = Field(default="", description="The current user message being processed")

    # Time context
    current_datetime: str = Field(
        default_factory=lambda: datetime.now().isoformat(), description="Current datetime in ISO format"
    )

    # User context
    user_context: Dict[str, Any] = Field(
        default_factory=dict, description="User context: location, timezone, preferences"
    )

    # Data items
    items: List[Dict[str, Any]] = Field(
        default_factory=list, description="Inbox items (emails, events) being processed"
    )

    # Agent outputs
    action_proposals: List[Dict[str, Any]] = Field(
        default_factory=list, description="Proposed actions awaiting approval"
    )
    agent_logs: List[Dict[str, Any]] = Field(default_factory=list, description="Logs from agent executions")

    # Legacy fields (for backward compatibility)
    user_preferences: Dict[str, Any] = Field(
        default_factory=dict, description="User preferences (deprecated, use user_context)"
    )
    weather_context: Dict[str, Any] = Field(default_factory=dict, description="Weather context for planning")

    # Error tracking
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Errors encountered during processing")

    # Flexible metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        arbitrary_types_allowed = True

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def add_message(self, role: str, content: str) -> None:
        """Add a message to conversation history."""
        self.conversation_history.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent messages from history."""
        return self.conversation_history[-limit:]

    def update_datetime(self) -> None:
        """Update current_datetime to now."""
        self.current_datetime = datetime.now().isoformat()

    def set_user_context(self, context: UserContext) -> None:
        """Set user context from a UserContext object."""
        self.user_context = context.model_dump()
        self.user_id = context.user_id

    def get_location(self) -> Dict[str, str]:
        """Get user's location from context."""
        return self.user_context.get("location", {})

    def get_timezone(self) -> str:
        """Get user's timezone from context."""
        return self.user_context.get("timezone", "UTC")

    @classmethod
    def create_for_chat(
        cls,
        user_message: str,
        user_id: str = "default",
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> "OpsAgentState":
        """
        Create a state object for a chat interaction.

        Args:
            user_message: The current user message
            user_id: User identifier
            conversation_history: Previous messages
            user_context: User context (location, timezone, etc.)

        Returns:
            Configured OpsAgentState for the chat
        """
        return cls(
            user_id=user_id,
            intent="conversation",
            current_message=user_message,
            conversation_history=conversation_history or [],
            current_datetime=datetime.now().isoformat(),
            user_context=user_context or {},
            metadata={"message": user_message},
        )


# ============================================================================
# State Factory Functions
# ============================================================================


def create_chat_state(
    message: str,
    session_history: Optional[List[Dict[str, str]]] = None,
    db_user=None,
) -> OpsAgentState:
    """
    Create a chat state from a message and optional history.

    Args:
        message: The user's message
        session_history: Previous messages from the session
        db_user: Database user model (optional)

    Returns:
        Configured OpsAgentState
    """
    # Build user context
    user_context = {}
    user_id = "default"

    if db_user:
        ctx = UserContext.from_db_user(db_user)
        user_context = ctx.model_dump()
        user_id = ctx.user_id

    # Build conversation history
    history = []
    if session_history:
        for msg in session_history:
            history.append(
                {
                    "role": msg.get("sender", msg.get("role", "user")),
                    "content": msg.get("content", ""),
                    "timestamp": msg.get("timestamp", datetime.now().isoformat()),
                }
            )

    return OpsAgentState(
        user_id=user_id,
        intent="conversation",
        current_message=message,
        conversation_history=history,
        current_datetime=datetime.now().isoformat(),
        user_context=user_context,
        metadata={"message": message},
    )


def create_workflow_state(
    intent: str,
    items: List[Dict[str, Any]],
    user_id: str = "default",
) -> OpsAgentState:
    """
    Create a state for a workflow execution (plan_day, refresh_inbox, etc.)

    Args:
        intent: The workflow intent
        items: Items to process
        user_id: User identifier

    Returns:
        Configured OpsAgentState for the workflow
    """
    return OpsAgentState(
        user_id=user_id,
        intent=intent,
        items=items,
        current_datetime=datetime.now().isoformat(),
    )
