"""
WebSocket manager for real-time updates.
Handles chat messages, action approvals, and live agent updates.
"""

import json
import logging
from typing import Dict, Set

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections with room-based subscriptions."""

    def __init__(self):
        # Map of room -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Map of WebSocket -> set of rooms
        self.connection_rooms: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket, room: str = "default"):
        """Connect a WebSocket and add to a room."""
        await websocket.accept()

        if room not in self.active_connections:
            self.active_connections[room] = set()

        self.active_connections[room].add(websocket)

        if websocket not in self.connection_rooms:
            self.connection_rooms[websocket] = set()
        self.connection_rooms[websocket].add(room)

        logger.info(f"WebSocket connected to room: {room}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        rooms = self.connection_rooms.pop(websocket, set())
        for room in rooms:
            self.active_connections.get(room, set()).discard(websocket)
            if not self.active_connections.get(room):
                del self.active_connections[room]

        logger.info("WebSocket disconnected")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast_to_room(self, message: dict, room: str):
        """Broadcast a message to all connections in a room."""
        if room not in self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections[room]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to room {room}: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

    async def subscribe(self, websocket: WebSocket, room: str):
        """Subscribe a connection to an additional room."""
        if websocket not in self.connection_rooms:
            await self.connect(websocket, room)
            return

        if room not in self.active_connections:
            self.active_connections[room] = set()

        self.active_connections[room].add(websocket)
        self.connection_rooms[websocket].add(room)

        await self.send_personal_message({"type": "subscribed", "room": room}, websocket)

    async def unsubscribe(self, websocket: WebSocket, room: str):
        """Unsubscribe a connection from a room."""
        if websocket in self.connection_rooms:
            self.connection_rooms[websocket].discard(room)

        if room in self.active_connections:
            self.active_connections[room].discard(websocket)
            if not self.active_connections[room]:
                del self.active_connections[room]


# Global connection manager instance
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, room: str = "default"):
    """WebSocket endpoint handler."""
    await manager.connect(websocket, room)

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type")

                if message_type == "subscribe":
                    room_name = message.get("room", "default")
                    await manager.subscribe(websocket, room_name)
                elif message_type == "unsubscribe":
                    room_name = message.get("room", "default")
                    await manager.unsubscribe(websocket, room_name)
                elif message_type == "ping":
                    await manager.send_personal_message({"type": "pong"}, websocket)
                else:
                    logger.warning(f"Unknown message type: {message_type}")

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(websocket)


# Event emission helpers
async def emit_chat_message(session_id: str, message: dict):
    """Emit a chat message to the chat room."""
    await manager.broadcast_to_room(
        {
            "type": "chat_message",
            "session_id": session_id,
            "data": message,
        },
        f"chat:{session_id}",
    )


async def emit_action_update(action_id: str, status: str, data: dict = None):
    """Emit an action status update."""
    await manager.broadcast_to_room(
        {
            "type": "action_update",
            "action_id": action_id,
            "status": status,
            "data": data or {},
        },
        "actions",
    )


async def emit_agent_update(agent_name: str, status: str, data: dict = None):
    """Emit an agent execution update."""
    await manager.broadcast_to_room(
        {
            "type": "agent_update",
            "agent_name": agent_name,
            "status": status,
            "data": data or {},
        },
        "agents",
    )


# Agent event streaming helpers
async def emit_agent_event(session_id: str, event: dict):
    """
    Emit an agent event to the session's agent room.

    This is the primary method for streaming real-time agent events.
    Clients subscribe to `agent:{session_id}` to receive these events.

    Event types:
    - reasoning: Agent chain of thought
    - tool_start: Tool execution beginning
    - tool_result: Tool execution result
    - tool_error: Tool execution failed
    - insight: Key discovery from data
    - plan: Execution plan
    - data: Data retrieved
    - decision: Agent decision point
    - progress: Overall progress update
    - agent_status: Agent state change
    - approval_required: Action needs approval
    - message: Final response
    - error: Something went wrong
    """
    room = f"agent:{session_id}"
    event["session_id"] = session_id
    await manager.broadcast_to_room(event, room)


async def emit_reasoning_event(session_id: str, step: str, content: str, tool: str = None, confidence: float = 1.0):
    """Emit a reasoning event showing agent's chain of thought."""
    await emit_agent_event(
        session_id,
        {
            "type": "reasoning",
            "step": step,
            "content": content,
            "tool": tool,
            "confidence": confidence,
        },
    )


async def emit_tool_event(
    session_id: str,
    tool_name: str,
    status: str,  # "started", "in_progress", "completed", "failed"
    args: dict = None,
    result: dict = None,
    progress_percent: int = None,
    duration_ms: int = None,
    error: str = None,
):
    """Emit a tool execution event."""
    await emit_agent_event(
        session_id,
        {
            "type": "tool_execution",
            "tool_name": tool_name,
            "status": status,
            "args": args or {},
            "result": result,
            "progress_percent": progress_percent,
            "duration_ms": duration_ms,
            "error": error,
        },
    )


async def emit_insight_event(
    session_id: str,
    content: str,
    source: str,
    importance: str = "medium",
):
    """Emit an insight event for key discoveries."""
    await emit_agent_event(
        session_id,
        {
            "type": "insight",
            "content": content,
            "source": source,
            "importance": importance,
        },
    )


async def emit_progress_event(
    session_id: str,
    current_step: int,
    total_steps: int,
    current_action: str,
):
    """Emit a progress update event."""
    percent = int((current_step / total_steps) * 100) if total_steps > 0 else 0
    await emit_agent_event(
        session_id,
        {
            "type": "progress",
            "current_step": current_step,
            "total_steps": total_steps,
            "percent_complete": percent,
            "current_action": current_action,
        },
    )


async def emit_approval_event(
    session_id: str,
    proposals: list,
    risk_level: str = "medium",
):
    """Emit an approval required event."""
    await emit_agent_event(
        session_id,
        {
            "type": "approval_required",
            "proposals": proposals,
            "risk_level": risk_level,
        },
    )


async def emit_message_event(
    session_id: str,
    content: str,
    metadata: dict = None,
):
    """Emit the final message response."""
    await emit_agent_event(
        session_id,
        {
            "type": "message",
            "content": content,
            "metadata": metadata or {},
        },
    )


async def emit_error_event(
    session_id: str,
    error: str,
    recoverable: bool = True,
):
    """Emit an error event."""
    await emit_agent_event(
        session_id,
        {
            "type": "error",
            "error": error,
            "recoverable": recoverable,
        },
    )


def get_manager() -> ConnectionManager:
    """Get the global connection manager."""
    return manager
