"""
Server-Sent Events (SSE) endpoints for real-time data updates.
Used for inbox, calendar, and weather updates.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict

from fastapi import Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.api.database import get_db

logger = logging.getLogger(__name__)


class SSEManager:
    """Manages SSE connections and broadcasts."""

    def __init__(self):
        self.connections: Dict[str, asyncio.Queue] = {}

    def add_connection(self, connection_id: str, queue: asyncio.Queue):
        """Add a new SSE connection."""
        self.connections[connection_id] = queue
        logger.info(f"SSE connection added: {connection_id}")

    def remove_connection(self, connection_id: str):
        """Remove an SSE connection."""
        if connection_id in self.connections:
            del self.connections[connection_id]
            logger.info(f"SSE connection removed: {connection_id}")

    async def broadcast(self, event_type: str, data: dict, channel: str = "default"):
        """Broadcast an event to all connections on a channel."""
        message = {
            "type": event_type,
            "channel": channel,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        for conn_id, queue in self.connections.items():
            try:
                await queue.put(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {conn_id}: {e}")
                self.remove_connection(conn_id)


# Global SSE manager
sse_manager = SSEManager()


async def sse_stream(connection_id: str, channel: str = "default") -> AsyncGenerator[str, None]:
    """Generate SSE stream for a connection."""
    queue = asyncio.Queue()
    sse_manager.add_connection(connection_id, queue)

    try:
        # Send initial connection message
        yield f"data: {json.dumps({'type': 'connected', 'channel': channel})}\n\n"

        while True:
            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {json.dumps(message)}\n\n"
            except asyncio.TimeoutError:
                # Send keepalive
                yield ": keepalive\n\n"

    except asyncio.CancelledError:
        logger.info(f"SSE stream cancelled: {connection_id}")
    except Exception as e:
        logger.error(f"SSE stream error: {e}", exc_info=True)
    finally:
        sse_manager.remove_connection(connection_id)


async def inbox_sse_endpoint(request: Request, db: Session = None):
    """SSE endpoint for inbox updates."""
    if db is None:
        db = next(get_db())

    connection_id = f"inbox_{id(request)}"

    async def event_generator():
        async for event in sse_stream(connection_id, "inbox"):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def calendar_sse_endpoint(request: Request, db: Session = None):
    """SSE endpoint for calendar updates."""
    if db is None:
        db = next(get_db())

    connection_id = f"calendar_{id(request)}"

    async def event_generator():
        async for event in sse_stream(connection_id, "calendar"):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def weather_sse_endpoint(request: Request):
    """SSE endpoint for weather updates."""
    connection_id = f"weather_{id(request)}"

    async def event_generator():
        async for event in sse_stream(connection_id, "weather"):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# Helper functions to emit events
async def emit_inbox_update(event_type: str, data: dict):
    """Emit an inbox update event."""
    await sse_manager.broadcast(event_type, data, "inbox")


async def emit_calendar_update(event_type: str, data: dict):
    """Emit a calendar update event."""
    await sse_manager.broadcast(event_type, data, "calendar")


async def emit_weather_update(event_type: str, data: dict):
    """Emit a weather update event."""
    await sse_manager.broadcast(event_type, data, "weather")
