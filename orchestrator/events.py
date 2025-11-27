"""
Rich Event Taxonomy for Real-Time Agent Progress Streaming

Provides 10+ event types for detailed visibility into agent reasoning,
tool execution, and decision-making processes.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentEvent(BaseModel):
    """Base class for all agent events."""

    type: str
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReasoningEvent(AgentEvent):
    """Agent reasoning step."""

    type: str = "reasoning"
    step: str
    content: str
    confidence: float = 1.0
    reasoning_chain: List[str] = Field(default_factory=list)


class ToolExecutionEvent(AgentEvent):
    """Tool execution progress."""

    type: str = "tool_execution"
    tool_name: str
    status: str
    args: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Any] = None
    progress_percent: Optional[int] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None


class InsightEvent(AgentEvent):
    """Key discovery or insight."""

    type: str = "insight"
    content: str
    source: str
    importance: str = "medium"
    related_data: Dict[str, Any] = Field(default_factory=dict)


class PlanEvent(AgentEvent):
    """Execution plan."""

    type: str = "plan"
    steps: List[str]
    estimated_duration_ms: Optional[int] = None
    parallel_groups: List[List[str]] = Field(default_factory=list)
    strategy: str = "sequential"


class DataEvent(AgentEvent):
    """Data retrieved."""

    type: str = "data"
    data_type: str
    count: int
    preview: List[Dict[str, Any]] = Field(default_factory=list)
    total_available: Optional[int] = None


class DecisionEvent(AgentEvent):
    """Agent decision point."""

    type: str = "decision"
    question: str
    choice: str
    reasoning: str
    alternatives: List[str] = Field(default_factory=list)
    confidence: float = 1.0


class ProgressEvent(AgentEvent):
    """Overall progress update."""

    type: str = "progress"
    current_step: int
    total_steps: int
    percent_complete: int
    current_action: str
    eta_ms: Optional[int] = None


class AgentStatusEvent(AgentEvent):
    """Agent state change."""

    type: str = "agent_status"
    status: str
    capabilities: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    message: Optional[str] = None


class ThoughtEvent(AgentEvent):
    """Agent internal thought."""

    type: str = "thought"
    content: str
    thought_type: str = "analysis"
    visibility: str = "user"


class ErrorEvent(AgentEvent):
    """Error occurred."""

    type: str = "error"
    error_type: str
    message: str
    stack_trace: Optional[str] = None
    recoverable: bool = True
    recovery_action: Optional[str] = None


class MessageEvent(AgentEvent):
    """Final response message."""

    type: str = "message"
    content: str
    role: str = "assistant"
    format: str = "markdown"


class ApprovalEvent(AgentEvent):
    """Action requiring approval."""

    type: str = "approval_required"
    proposals: List[Dict[str, Any]]
    risk_level: str = "medium"
    auto_approve: bool = False


EVENT_TYPE_MAP = {
    "reasoning": ReasoningEvent,
    "tool_execution": ToolExecutionEvent,
    "insight": InsightEvent,
    "plan": PlanEvent,
    "data": DataEvent,
    "decision": DecisionEvent,
    "progress": ProgressEvent,
    "agent_status": AgentStatusEvent,
    "thought": ThoughtEvent,
    "error": ErrorEvent,
    "message": MessageEvent,
    "approval_required": ApprovalEvent,
}


def create_event(event_type: str, **kwargs) -> AgentEvent:
    """
    Create an event of the specified type.

    Args:
        event_type: Type of event to create
        **kwargs: Event-specific parameters

    Returns:
        Instantiated event
    """
    event_class = EVENT_TYPE_MAP.get(event_type, AgentEvent)
    return event_class(type=event_type, **kwargs)


def event_to_dict(event: AgentEvent) -> Dict[str, Any]:
    """Convert event to dictionary for serialization."""
    data = event.model_dump()
    data["timestamp"] = event.timestamp.isoformat()
    return data


def dict_to_event(data: Dict[str, Any]) -> AgentEvent:
    """Convert dictionary to event."""
    event_type = data.get("type", "agent_event")
    event_class = EVENT_TYPE_MAP.get(event_type, AgentEvent)

    if "timestamp" in data and isinstance(data["timestamp"], str):
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])

    return event_class(**data)
