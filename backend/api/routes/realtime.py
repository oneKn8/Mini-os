"""
Real-time endpoints: WebSocket and SSE routes.

Supports:
- General WebSocket rooms for real-time updates
- Agent event streaming via `agent:{session_id}` rooms
- SSE endpoints for inbox, calendar, and weather
"""

from fastapi import APIRouter, Depends, Request, WebSocket
from sqlalchemy.orm import Session

from backend.api.database import get_db
from backend.api.sse import (
    calendar_sse_endpoint,
    inbox_sse_endpoint,
    weather_sse_endpoint,
)
from backend.api.websocket import websocket_endpoint, manager

router = APIRouter(prefix="/realtime", tags=["realtime"])


@router.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    # Get room from query parameter or default
    room = websocket.query_params.get("room", "default")
    await websocket_endpoint(websocket, room)


@router.websocket("/ws/{room}")
async def websocket_room_route(websocket: WebSocket, room: str):
    """WebSocket endpoint for specific room."""
    await websocket_endpoint(websocket, room)


@router.websocket("/agent/{session_id}")
async def agent_websocket_route(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for agent event streaming.

    Clients connect here to receive real-time agent events for a specific chat session.
    Events streamed:
    - reasoning: Agent chain of thought
    - tool_execution: Tool start/progress/complete/error
    - insight: Key discoveries
    - plan: Execution plan
    - progress: Overall progress
    - agent_status: Agent state changes
    - approval_required: Actions needing approval
    - message: Final response
    """
    room = f"agent:{session_id}"
    await websocket_endpoint(websocket, room)


@router.get("/status")
async def realtime_status():
    """Get status of real-time connections."""
    return {
        "rooms": list(manager.active_connections.keys()),
        "total_connections": sum(len(conns) for conns in manager.active_connections.values()),
        "room_counts": {room: len(conns) for room, conns in manager.active_connections.items()},
    }


@router.get("/sse/inbox")
async def sse_inbox(request: Request, db: Session = Depends(get_db)):
    """SSE endpoint for inbox updates."""
    return await inbox_sse_endpoint(request, db)


@router.get("/sse/calendar")
async def sse_calendar(request: Request, db: Session = Depends(get_db)):
    """SSE endpoint for calendar updates."""
    return await calendar_sse_endpoint(request, db)


@router.get("/sse/weather")
async def sse_weather(request: Request):
    """SSE endpoint for weather updates."""
    return await weather_sse_endpoint(request)
