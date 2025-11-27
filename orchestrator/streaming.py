"""
Agent Streaming Session for Real-Time Event Emission

Manages real-time streaming of agent execution events with WebSocket support.
"""

import logging
from typing import AsyncIterator, Dict, List
from datetime import datetime

from orchestrator.events import (
    AgentEvent,
    ReasoningEvent,
    ToolExecutionEvent,
    ProgressEvent,
    AgentStatusEvent,
    event_to_dict,
)

logger = logging.getLogger(__name__)


class AgentStreamingSession:
    """
    Manages real-time streaming of agent execution.

    Features:
    - Event buffering with history
    - WebSocket broadcasting
    - Progress tracking
    - Error recovery
    """

    def __init__(self, session_id: str, agent_id: str):
        """
        Initialize streaming session.

        Args:
            session_id: Session identifier
            agent_id: Agent identifier
        """
        self.session_id = session_id
        self.agent_id = agent_id
        self.event_buffer: List[AgentEvent] = []
        self.start_time = datetime.now()
        self.total_steps = 0
        self.current_step = 0
        self.ws_manager = None

    def set_websocket_manager(self, ws_manager):
        """Set WebSocket manager for broadcasting."""
        self.ws_manager = ws_manager

    async def emit_event(self, event: AgentEvent):
        """
        Emit an event to all subscribers.

        Args:
            event: Event to emit
        """
        event.agent_id = self.agent_id
        event.session_id = self.session_id

        self.event_buffer.append(event)

        event_dict = event_to_dict(event)

        if self.ws_manager:
            try:
                await self.ws_manager.broadcast_to_room(event_dict, f"agent:{self.session_id}")
            except Exception as e:
                logger.error(f"Failed to broadcast event: {e}")

        return event_dict

    async def emit_reasoning(self, step: str, content: str, confidence: float = 1.0) -> Dict:
        """Emit a reasoning event."""
        event = ReasoningEvent(step=step, content=content, confidence=confidence, reasoning_chain=[])
        return await self.emit_event(event)

    async def emit_tool_start(self, tool_name: str, args: Dict) -> Dict:
        """Emit tool execution start event."""
        event = ToolExecutionEvent(tool_name=tool_name, status="started", args=args)
        return await self.emit_event(event)

    async def emit_tool_progress(self, tool_name: str, progress_percent: int, message: str = "") -> Dict:
        """Emit tool progress update."""
        event = ToolExecutionEvent(
            tool_name=tool_name,
            status="in_progress",
            args={},
            progress_percent=progress_percent,
            metadata={"message": message},
        )
        return await self.emit_event(event)

    async def emit_tool_complete(self, tool_name: str, result: any, duration_ms: int) -> Dict:
        """Emit tool completion event."""
        event = ToolExecutionEvent(
            tool_name=tool_name,
            status="completed",
            args={},
            result=result,
            duration_ms=duration_ms,
        )
        return await self.emit_event(event)

    async def emit_tool_error(self, tool_name: str, error: str) -> Dict:
        """Emit tool error event."""
        event = ToolExecutionEvent(tool_name=tool_name, status="failed", args={}, error=error)
        return await self.emit_event(event)

    async def emit_progress(self, current_step: int, total_steps: int, current_action: str) -> Dict:
        """Emit progress update."""
        self.current_step = current_step
        self.total_steps = total_steps

        percent_complete = int((current_step / total_steps) * 100) if total_steps > 0 else 0

        elapsed_ms = int((datetime.now() - self.start_time).total_seconds() * 1000)
        eta_ms = None
        if current_step > 0:
            avg_ms_per_step = elapsed_ms / current_step
            remaining_steps = total_steps - current_step
            eta_ms = int(avg_ms_per_step * remaining_steps)

        event = ProgressEvent(
            current_step=current_step,
            total_steps=total_steps,
            percent_complete=percent_complete,
            current_action=current_action,
            eta_ms=eta_ms,
        )
        return await self.emit_event(event)

    async def emit_agent_status(
        self, status: str, capabilities: List[str] = None, tools: List[str] = None, message: str = None
    ) -> Dict:
        """Emit agent status change."""
        event = AgentStatusEvent(
            status=status,
            capabilities=capabilities or [],
            tools=tools or [],
            message=message,
        )
        return await self.emit_event(event)

    async def stream_agent_execution(self, agent, context, user_message: str) -> AsyncIterator[Dict]:
        """
        Stream agent execution with rich progress updates.

        Args:
            agent: Agent to execute
            context: Execution context
            user_message: User's message

        Yields:
            Event dictionaries
        """
        try:
            await self.emit_agent_status(
                "initializing",
                capabilities=getattr(agent, "capabilities", []),
                tools=[t.name for t in getattr(agent, "tools", [])],
            )

            if hasattr(agent, "stream"):
                async for event in agent.stream(user_message, context):
                    if isinstance(event, dict):
                        yield event
                    else:
                        event_dict = event_to_dict(event) if hasattr(event, "model_dump") else event
                        yield await self.emit_event(event_dict)
            else:
                await self.emit_agent_status("executing")

                result = await agent.run(context)

                yield await self.emit_event(
                    {
                        "type": "message",
                        "content": result.output_summary.get("response", "Task completed"),
                    }
                )

            await self.emit_agent_status("completed")

        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            yield await self.emit_event(
                {
                    "type": "error",
                    "error_type": "execution_error",
                    "message": str(e),
                    "recoverable": False,
                }
            )

    def get_event_history(self) -> List[Dict]:
        """Get all events from this session."""
        return [event_to_dict(e) for e in self.event_buffer]

    def clear_history(self):
        """Clear event history."""
        self.event_buffer.clear()

    def get_session_duration_ms(self) -> int:
        """Get session duration in milliseconds."""
        return int((datetime.now() - self.start_time).total_seconds() * 1000)

    def __repr__(self) -> str:
        return (
            "AgentStreamingSession("
            f"session_id={self.session_id}, agent_id={self.agent_id}, "
            f"events={len(self.event_buffer)})"
        )
