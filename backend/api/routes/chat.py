"""
Chat API routes enabling conversational control over the multi-agent system.

Refactored to use the ConversationalAgent with dynamic tool-based reasoning
instead of rigid keyword-based intent detection.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.api.database import get_db
from backend.api.models import ActionProposal, ChatMessageEntry, ChatSession, Item, User
from orchestrator.agents.conversational_agent import ConversationalAgent
from orchestrator.state import UserContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


# ============================================================================
# DTOs and Request/Response Models
# ============================================================================


class ChatMessageDTO(BaseModel):
    """Pydantic model for chat messages."""

    id: str
    content: str
    sender: Literal["user", "assistant"]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class SendMessageRequest(BaseModel):
    """Incoming chat message request body."""

    content: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = Field(default=None, alias="sessionId")
    context: Optional[Dict[str, Any]] = None
    model_provider: Optional[str] = Field(default=None, alias="modelProvider")
    model_name: Optional[str] = Field(default=None, alias="modelName")

    class Config:
        populate_by_name = True


class SendMessageResponse(BaseModel):
    """Response payload for chat message endpoint."""

    message: ChatMessageDTO
    session_id: str = Field(..., alias="sessionId")

    class Config:
        populate_by_name = True


class ChatServiceError(Exception):
    """Raised when the chat service fails to fulfill a request."""


# ============================================================================
# Session Management
# ============================================================================


class ChatSessionStore:
    """Persistence layer for chat sessions and messages."""

    def get_or_create(self, db: Session, session_id: Optional[str]) -> ChatSession:
        existing = None
        if session_id:
            existing = self.get_session(db, session_id)
        if existing:
            return existing

        session = ChatSession()
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def get_session(self, db: Session, session_id: str) -> Optional[ChatSession]:
        session_uuid = self._parse_session_id(session_id)
        if not session_uuid:
            return None
        return db.query(ChatSession).filter(ChatSession.id == session_uuid).first()

    def update_title(self, db: Session, session: ChatSession, title: str) -> None:
        """Update the session title."""
        session.title = title[:200] if title else None  # Limit to 200 chars
        db.commit()

    def generate_title_from_message(self, content: str) -> str:
        """
        Generate a meaningful title from the first user message.

        Strategy:
        - For questions, use the core question
        - For commands, describe the action
        - Truncate to reasonable length
        """
        content = content.strip()

        # Remove common prefixes
        for prefix in ["can you ", "please ", "could you ", "i want to ", "i need to ", "help me "]:
            if content.lower().startswith(prefix):
                content = content[len(prefix) :]
                break

        # Capitalize first letter
        if content:
            content = content[0].upper() + content[1:]

        # Common task patterns
        task_patterns = {
            "weather": "Weather check",
            "calendar": "Calendar query",
            "schedule": "Schedule review",
            "email": "Email search",
            "inbox": "Inbox review",
            "plan": "Day planning",
            "meeting": "Meeting prep",
            "remind": "Reminder",
            "priority": "Priority check",
        }

        content_lower = content.lower()
        for keyword, title in task_patterns.items():
            if keyword in content_lower and len(content) > 50:
                # If message is long and contains keyword, use short title
                return title

        # Truncate long messages
        if len(content) > 50:
            # Try to cut at a natural break
            truncated = content[:50]
            last_space = truncated.rfind(" ")
            if last_space > 30:
                truncated = truncated[:last_space]
            return truncated + "..."

        return content if content else "New conversation"

    def append_message(
        self,
        db: Session,
        session: ChatSession,
        sender: Literal["user", "assistant"],
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ChatMessageEntry:
        entry = ChatMessageEntry(session_id=session.id, sender=sender, content=content, message_metadata=metadata)
        db.add(entry)
        db.commit()
        db.refresh(entry)

        # Auto-generate title from first user message
        if sender == "user" and not session.title:
            title = self.generate_title_from_message(content)
            self.update_title(db, session, title)

        return entry

    def list_messages(self, db: Session, session: ChatSession) -> List[ChatMessageEntry]:
        return (
            db.query(ChatMessageEntry)
            .filter(ChatMessageEntry.session_id == session.id)
            .order_by(ChatMessageEntry.created_at.asc())
            .all()
        )

    def get_conversation_history(self, db: Session, session: ChatSession, limit: int = 20) -> List[Dict[str, str]]:
        """Get conversation history in format suitable for the agent."""
        messages = (
            db.query(ChatMessageEntry)
            .filter(ChatMessageEntry.session_id == session.id)
            .order_by(ChatMessageEntry.created_at.desc())
            .limit(limit)
            .all()
        )
        # Reverse to get chronological order
        messages = list(reversed(messages))
        return [
            {
                "role": msg.sender,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat() if msg.created_at else "",
            }
            for msg in messages
        ]

    def _parse_session_id(self, session_id: str) -> Optional[uuid.UUID]:
        try:
            return uuid.UUID(str(session_id))
        except (ValueError, TypeError):
            return None


# ============================================================================
# Chat Service (using ConversationalAgent)
# ============================================================================


class ChatService:
    """
    High-level chat service using the ConversationalAgent.

    This replaces the old keyword-based intent detection with
    a dynamic tool-calling agent that can handle any type of request.
    """

    def __init__(self):
        self._agent: Optional[ConversationalAgent] = None

    def _get_agent(self) -> ConversationalAgent:
        """Get or create the conversational agent."""
        if self._agent is None:
            self._agent = ConversationalAgent()
        return self._agent

    def _get_user_context(self, db: Session) -> Dict[str, Any]:
        """Build user context from database."""
        try:
            user = db.query(User).first()
            if user:
                ctx = UserContext.from_db_user(user)
                return ctx.model_dump()
        except Exception as e:
            logger.warning(f"Failed to load user context: {e}")
        return {}

    async def handle_message(
        self,
        message: str,
        db: Session,
        conversation_history: List[Dict[str, str]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Handle a chat message using the conversational agent.

        Args:
            message: User's message
            db: Database session
            conversation_history: Previous messages
            context: Additional context from frontend

        Returns:
            Tuple of (response_text, metadata)
        """
        agent = self._get_agent()
        user_context = self._get_user_context(db)

        # Merge frontend context with user context
        if context:
            user_context.update(context)

        try:
            # Use the agent's streaming interface but collect the full response
            full_response = ""
            tools_used = []
            proposals = []

            async for event in agent.stream(
                user_message=message,
                conversation_history=conversation_history,
                user_context=user_context,
            ):
                if event["type"] == "response":
                    full_response = event.get("content", "")
                    tools_used = event.get("tools_used", [])
                    proposals = event.get("proposals", [])

            metadata = {
                "tools_used": tools_used,
                "requires_approval": len(proposals) > 0,
                "proposals": proposals,
            }

            return full_response, metadata

        except Exception as e:
            logger.error(f"Agent error: {e}", exc_info=True)
            return ("I encountered an error processing your request. Please try again.", {"error": str(e)})

    async def stream_message(
        self,
        message: str,
        db: Session,
        conversation_history: List[Dict[str, str]],
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Stream chat response with visible reasoning and intermediate events.

        Yields events for:
        - reasoning: Agent's chain of thought (visible to user)
        - tool_start: Tool is being called
        - tool_result: Tool returned results
        - insight: Key insights from data
        - response: Final response
        - suggestions: Follow-up suggestions
        - error: Something went wrong
        """
        agent = self._get_agent()
        user_context = self._get_user_context(db)

        if context:
            user_context.update(context)

        try:
            async for event in agent.stream(
                user_message=message,
                conversation_history=conversation_history,
                user_context=user_context,
            ):
                # Pass through agent events with enhanced formatting
                event_type = event.get("type", "")

                if event_type == "reasoning":
                    # Chain of thought - visible reasoning to user
                    yield {
                        "type": "reasoning",
                        "content": event.get("content", ""),
                        "step": event.get("step", "thinking"),
                        "tool": event.get("tool"),
                    }
                elif event_type == "thinking":
                    # Legacy thinking event
                    yield {
                        "type": "reasoning",
                        "content": event.get("content", "Processing..."),
                        "step": "thinking",
                    }
                elif event_type == "tool_start":
                    yield {
                        "type": "tool_start",
                        "tool": event.get("tool", "tool"),
                        "action": event.get("action", "Processing"),
                        "icon": event.get("icon", ""),
                        "args": event.get("args", {}),
                    }
                elif event_type == "tool_result":
                    yield {
                        "type": "tool_result",
                        "tool": event.get("tool", "tool"),
                        "icon": event.get("icon", ""),
                        "result": event.get("result", {}),
                        "success": event.get("success", True),
                    }
                elif event_type == "tool_error":
                    yield {
                        "type": "tool_error",
                        "tool": event.get("tool", "tool"),
                        "error": event.get("error", "Unknown error"),
                    }
                elif event_type == "insight":
                    # Key insight extracted from tool results
                    yield {
                        "type": "insight",
                        "content": event.get("content", ""),
                        "source": event.get("source", ""),
                    }
                elif event_type == "suggestions":
                    # Follow-up suggestions
                    yield {
                        "type": "suggestions",
                        "actions": event.get("actions", []),
                    }
                elif event_type == "response":
                    # Check for pending approvals
                    proposals = event.get("proposals", [])
                    if proposals:
                        yield {
                            "type": "approval_required",
                            "agent": "conversational",
                            "proposals": proposals,
                        }

                    yield {
                        "type": "message",
                        "content": event.get("content", ""),
                        "metadata": {
                            "tools_used": event.get("tools_used", []),
                            "requires_approval": event.get("requires_approval", False),
                        },
                    }
                elif event_type == "error":
                    yield {
                        "type": "error",
                        "error": event.get("error", "Unknown error"),
                    }

        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield {
                "type": "error",
                "error": str(e),
            }
            yield {
                "type": "message",
                "content": "I encountered an error. Please try again.",
                "metadata": {"error": str(e)},
            }


# ============================================================================
# Singletons
# ============================================================================

session_store = ChatSessionStore()
chat_service = ChatService()


# ============================================================================
# Helper Functions
# ============================================================================


def _serialize_record(record: ChatMessageEntry) -> ChatMessageDTO:
    return ChatMessageDTO(
        id=str(record.id),
        content=record.content,
        sender=record.sender,  # type: ignore[arg-type]
        timestamp=record.created_at or datetime.now(timezone.utc),
        metadata=record.message_metadata,
    )


def _serialize_datetime(obj: Any) -> Any:
    """Recursively convert datetime objects to ISO strings."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_datetime(item) for item in obj]
    return obj


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/message", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest, db: Session = Depends(get_db)):
    """
    Primary entrypoint for chat messages.

    Uses the ConversationalAgent to dynamically handle any type of request
    including planning, weather, email search, calendar, and general questions.
    """
    content = request.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    chat_session = session_store.get_or_create(db, request.session_id)
    session_id = str(chat_session.id)

    # Get conversation history
    history = session_store.get_conversation_history(db, chat_session, limit=20)

    # Record user message
    session_store.append_message(
        db,
        chat_session,
        "user",
        content,
        metadata={"context": request.context} if request.context else None,
    )

    try:
        reply_text, metadata = await chat_service.handle_message(content, db, history, request.context)
    except ChatServiceError as exc:
        logger.error("Chat service failed: %s", exc)
        reply_text = str(exc) or "I ran into a problem processing that request."
        metadata = {"error": True}
    except Exception as exc:
        logger.exception("Unexpected chat failure: %s", exc)
        reply_text = "Something went wrong. Please try again shortly."
        metadata = {"error": True}

    # Serialize metadata to handle datetime objects
    metadata = _serialize_datetime(metadata)

    assistant_record = session_store.append_message(db, chat_session, "assistant", reply_text, metadata)

    return SendMessageResponse(message=_serialize_record(assistant_record), session_id=session_id)


@router.post("/stream")
async def stream_chat(request: SendMessageRequest, db: Session = Depends(get_db)):
    """
    Stream chat responses with intermediate agent thoughts.

    Events streamed:
    - session_id: Initial session identifier
    - thought: Agent thinking/tool execution updates
    - approval_required: Actions needing user approval
    - message: Final response
    - error: Error occurred
    """
    content = request.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    chat_session = session_store.get_or_create(db, request.session_id)
    session_id = str(chat_session.id)

    # Get conversation history
    history = session_store.get_conversation_history(db, chat_session, limit=20)

    # Record user message
    session_store.append_message(
        db,
        chat_session,
        "user",
        content,
        metadata={"context": request.context} if request.context else None,
    )

    # Build context
    ctx = request.context or {}
    if request.model_provider:
        ctx["model_provider"] = request.model_provider
    if request.model_name:
        ctx["model_name"] = request.model_name

    async def event_generator():
        full_response_text = ""
        metadata = {}

        try:
            # Yield session ID first
            yield json.dumps({"type": "session_id", "session_id": session_id}) + "\n"

            async for event in chat_service.stream_message(content, db, history, ctx):
                # Serialize any datetime objects in the event
                serialized_event = _serialize_datetime(event)
                yield json.dumps(serialized_event, default=str) + "\n"

                if event.get("type") == "message":
                    full_response_text = event.get("content", "")
                    metadata = event.get("metadata", {})

            # Store assistant message after stream completes
            if full_response_text:
                metadata["streamed"] = True
                session_store.append_message(
                    db, chat_session, "assistant", full_response_text, _serialize_datetime(metadata)
                )

        except Exception as exc:
            logger.exception("Streaming error: %s", exc)
            yield json.dumps({"type": "error", "error": str(exc)}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


@router.get("/sessions")
async def get_sessions(limit: int = 20, db: Session = Depends(get_db)):
    """List recent chat sessions with their titles."""
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.status == "active")
        .order_by(ChatSession.updated_at.desc())
        .limit(limit)
        .all()
    )

    result = []
    for s in sessions:
        # Use the stored title, or generate a fallback
        title = s.title
        if not title:
            # Try to get title from first message
            first_msg = (
                db.query(ChatMessageEntry)
                .filter(ChatMessageEntry.session_id == s.id, ChatMessageEntry.sender == "user")
                .order_by(ChatMessageEntry.created_at.asc())
                .first()
            )
            if first_msg:
                title = session_store.generate_title_from_message(first_msg.content)
                # Update the session with the generated title
                s.title = title
                db.commit()
            else:
                title = f"Chat {s.created_at.strftime('%b %d, %H:%M')}" if s.created_at else "New Chat"

        result.append(
            {
                "id": str(s.id),
                "title": title,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                "message_count": db.query(ChatMessageEntry).filter(ChatMessageEntry.session_id == s.id).count(),
            }
        )

    return result


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    """Get full chat history for a session."""
    session = session_store.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = session_store.list_messages(db, session)

    return [
        {
            "id": str(msg.id),
            "content": msg.content,
            "sender": msg.sender,
            "timestamp": msg.created_at.isoformat() if msg.created_at else None,
            "metadata": msg.message_metadata,
        }
        for msg in messages
    ]


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a chat session and all its messages."""
    session = session_store.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Soft delete by marking as archived
    session.status = "archived"
    db.commit()

    return {"status": "deleted", "session_id": session_id}


@router.post("/action/{action_id}/approve")
async def approve_action(action_id: str, request: Dict[str, bool], db: Session = Depends(get_db)):
    """Handle user approval/rejection of an action."""
    approved = request.get("approved", False)

    proposal = db.query(ActionProposal).filter(ActionProposal.id == action_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Action proposal not found")

    if proposal.status != "pending":
        return {"message": f"Action already {proposal.status}"}

    proposal.status = "approved" if approved else "rejected"
    proposal.approved_at = datetime.now(timezone.utc) if approved else None
    db.commit()

    return {"status": proposal.status, "action_id": action_id}


@router.post("/resume")
async def resume_workflow(request: Dict[str, Any], db: Session = Depends(get_db)):
    """Resume workflow execution after approval."""
    session_id = request.get("sessionId") or request.get("session_id")

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    chat_session = session_store.get_session(db, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # For now, return success - the approved action will be executed
    # when the user sends the next message
    async def event_generator():
        yield json.dumps(
            {
                "type": "message",
                "content": "Actions have been approved. They will be executed shortly.",
                "metadata": {"resumed": True},
            }
        ) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


@router.get("/history/{session_id}", response_model=List[ChatMessageDTO])
async def get_history(session_id: str, db: Session = Depends(get_db)):
    """Return stored chat history for a session."""
    session = session_store.get_session(db, session_id)
    if not session:
        return []

    records = session_store.list_messages(db, session)
    return [_serialize_record(record) for record in records]


@router.get("/pending-actions")
async def get_pending_actions(limit: int = 10, db: Session = Depends(get_db)):
    """Get all pending actions awaiting approval."""
    proposals = (
        db.query(ActionProposal)
        .filter(ActionProposal.status == "pending")
        .order_by(ActionProposal.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": str(p.id),
            "action_type": p.action_type,
            "agent_name": p.agent_name,
            "explanation": p.explanation,
            "risk_level": p.risk_level,
            "payload": p.payload,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in proposals
    ]
