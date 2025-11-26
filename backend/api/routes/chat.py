"""
Chat API routes enabling conversational control over the multi-agent system.
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple

import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.api.database import get_db
from backend.api.models import ActionProposal, ChatMessageEntry, ChatSession, Item
from orchestrator.llm_client import LLMClient
from orchestrator.orchestrator import Orchestrator, OrchestrationResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessageDTO(BaseModel):
    """Pydantic model for chat messages."""

    id: str
    content: str
    sender: Literal["user", "assistant"]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class SendMessageRequest(BaseModel):
    """Incoming chat message request body."""

    content: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = Field(default=None, alias="sessionId")
    context: Optional[Dict[str, Any]] = None
    # Added model preference
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


@dataclass
class IntentMatch:
    """Represents detected intent for a chat message."""

    intent: str
    confidence: float
    reason: str = ""


class LLMIntentClassifier:
    """Uses the configured LLM provider to classify chat intent when keywords are insufficient."""

    def __init__(self):
        self.client = LLMClient()

    def classify(self, text: str, context: Optional[Dict[str, Any]] = None) -> IntentMatch:
        context_snippet = ""
        if context:
            context_snippet = f"Context: {context}\n"

        prompt = f"""Determine the user's intent for a multi-agent productivity assistant.
{context_snippet}
Message: \"\"\"{text}\"\"\"

Respond with JSON:
{{
  "intent": "plan_day|refresh_inbox|pending_actions|help|general",
  "confidence": 0.0-1.0,
  "reason": "short explanation"
}}

Intent guide:
- 'plan_day': User wants to plan their day or get an agenda
- 'refresh_inbox': User wants to triage/process/refresh inbox
- 'pending_actions': User wants to see items awaiting their approval
- 'help': User asks what you can do or how to use the system (e.g. "what can you do?", "help me")
- 'general': Any factual question, request for information, or anything else
  (e.g. "what is X?", "when is Y?", "tell me about Z")

IMPORTANT: Use 'general' for questions asking about facts, policies, dates,
limits, etc. Only use 'help' when the user specifically asks about the
assistant's capabilities."""

        result = self.client.call_json(prompt, temperature=0.0, max_tokens=256)

        intent = result.get("intent", "general")
        confidence = float(result.get("confidence", 0.4))
        reason = result.get("reason", "llm_classifier")

        return IntentMatch(intent=intent, confidence=confidence, reason=reason)


class ChatIntentDetector:
    """Intent detector that uses keywords first and falls back to the LLM classifier."""

    def __init__(self, enable_llm: bool = True):
        self._llm_classifier: Optional[LLMIntentClassifier] = None
        if enable_llm:
            try:
                self._llm_classifier = LLMIntentClassifier()
            except Exception as exc:
                logger.warning("LLM intent classifier unavailable: %s", exc)
                self._llm_classifier = None

    def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> IntentMatch:
        normalized = (text or "").strip().lower()
        if not normalized:
            return IntentMatch(intent="general", confidence=0.0, reason="empty_message")

        keyword_match = self._keyword_match(normalized, context)

        if keyword_match.confidence >= 0.7 or not self._llm_classifier:
            return keyword_match

        try:
            llm_match = self._llm_classifier.classify(text, context)
            if llm_match and llm_match.confidence >= keyword_match.confidence:
                return llm_match
        except Exception as exc:
            logger.warning("LLM intent classification failed: %s", exc)

        return keyword_match

    def _keyword_match(self, normalized: str, context: Optional[Dict[str, Any]]) -> IntentMatch:
        if any(
            phrase in normalized
            for phrase in [
                "plan my day",
                "plan today",
                "plan out my day",
                "today's plan",
                "schedule my day",
                "daily plan",
            ]
        ):
            return IntentMatch(intent="plan_day", confidence=0.95, reason="plan_keywords")

        if "plan" in normalized and ("day" in normalized or "today" in normalized):
            return IntentMatch(intent="plan_day", confidence=0.8, reason="plan_word_pair")

        if any(word in normalized for word in ["refresh", "process", "catch up", "triage"]) and "inbox" in normalized:
            return IntentMatch(intent="refresh_inbox", confidence=0.85, reason="inbox_keywords")

        if "inbox" in normalized and "update" in normalized:
            return IntentMatch(intent="refresh_inbox", confidence=0.75, reason="inbox_update")

        pending_keywords = ["pending actions", "approvals", "review actions", "approve actions", "needs approval"]
        if any(phrase in normalized for phrase in pending_keywords):
            return IntentMatch(intent="pending_actions", confidence=0.85, reason="pending_keywords")

        if "actions" in normalized and any(k in normalized for k in ["pending", "approve", "show", "list", "need"]):
            return IntentMatch(intent="pending_actions", confidence=0.75, reason="actions_context")

        if "what can you do" in normalized or normalized.startswith("help") or "how can you help" in normalized:
            return IntentMatch(intent="help", confidence=0.7, reason="help_keywords")

        if context and context.get("currentView") == "/actions" and "show" in normalized:
            return IntentMatch(intent="pending_actions", confidence=0.65, reason="actions_view_context")

        return IntentMatch(intent="general", confidence=0.3, reason="default")


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
        return entry

    def list_messages(self, db: Session, session: ChatSession) -> List[ChatMessageEntry]:
        return (
            db.query(ChatMessageEntry)
            .filter(ChatMessageEntry.session_id == session.id)
            .order_by(ChatMessageEntry.created_at.asc())
            .all()
        )

    def _parse_session_id(self, session_id: str) -> Optional[uuid.UUID]:
        try:
            return uuid.UUID(str(session_id))
        except (ValueError, TypeError):
            return None


class ChatService:
    """High-level service that routes chat commands to orchestrator functions."""

    def __init__(self):
        self._orchestrator: Optional[Orchestrator] = None
        self.intent_detector = ChatIntentDetector()

    async def handle_message(
        self, message: str, db: Session, context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        intent_match = self.intent_detector.detect(message, context)

        handlers = {
            "plan_day": self._handle_plan_day,
            "refresh_inbox": self._handle_refresh_inbox,
            "pending_actions": self._handle_pending_actions,
            "help": self._handle_help,
        }

        handler = handlers.get(intent_match.intent)
        if handler:
            return await handler(intent_match, db, context)

        return await self._handle_general(message, intent_match, db, context)

    async def stream_message(self, message: str, db: Session, context: Optional[Dict[str, Any]] = None):
        intent_match = self.intent_detector.detect(message, context)

        # Yield intent detection info
        yield {"type": "intent", "intent": intent_match.intent, "confidence": intent_match.confidence}

        if intent_match.intent == "general":
            response, metadata = await self._handle_general(message, intent_match, db, context)
            yield {"type": "message", "content": response, "metadata": metadata}
            return

        if intent_match.intent == "help":
            response, metadata = await self._handle_help(intent_match, db, context)
            yield {"type": "message", "content": response, "metadata": metadata}
            return

        if intent_match.intent == "pending_actions":
            response, metadata = await self._handle_pending_actions(intent_match, db, context)
            yield {"type": "message", "content": response, "metadata": metadata}
            return

        # For agent workflows (plan_day, refresh_inbox)
        orchestrator = self._get_orchestrator()
        items = []
        if intent_match.intent in ["plan_day", "refresh_inbox"]:
            items = self._load_recent_items(db, limit=50)
            if not items and intent_match.intent == "plan_day":
                yield {"type": "error", "error": "I need at least a few inbox items before I can plan your day."}
                return
            if not items and intent_match.intent == "refresh_inbox":
                yield {"type": "error", "error": "I don't have any inbox items to triage yet."}
                return

        agent_context = orchestrator.build_context(intent=intent_match.intent, items=items, user_id="default_user")

        final_results = {}

        async for event in orchestrator.stream(intent_match.intent, agent_context, db):
            yield event

            if event["type"] == "thought" and event.get("status") == "success":
                agent = event["agent"]
                summary = event.get("summary")
                if summary:
                    final_results[agent] = summary

        # Format final response based on intent
        response_text = "Process completed."
        if intent_match.intent == "plan_day":
            planner_summary = final_results.get("planner", {})
            response_text = self._format_plan_summary(planner_summary)
        elif intent_match.intent == "refresh_inbox":
            response_text = "Refresh complete.\n"
            for agent, summary in final_results.items():
                summary_str = ", ".join([f"{k}: {v}" for k, v in summary.items()])
                response_text += f"- {agent}: {summary_str}\n"

        yield {"type": "message", "content": response_text, "metadata": {"intent": intent_match.intent}}

    async def _handle_plan_day(
        self, intent: IntentMatch, db: Session, context: Optional[Dict[str, Any]]
    ) -> Tuple[str, Dict[str, Any]]:
        orchestrator = self._get_orchestrator()
        items = self._load_recent_items(db, limit=50)

        if not items:
            raise ChatServiceError("I need at least a few inbox items before I can plan your day.")

        agent_context = orchestrator.build_context(intent="plan_day", items=items, user_id="default_user")
        result = await orchestrator.run("plan_day", agent_context)

        planner_result = result.results.get("planner") if result.results else None
        plan_data = {}
        if planner_result:
            plan_data = planner_result.output_summary or {}

        if not plan_data:
            raise ChatServiceError("The planner agent didn't return a plan. Try again in a moment.")

        response = self._format_plan_summary(plan_data)
        metadata = {
            "intent": "plan_day",
            "function_call": True,
            "result": plan_data,
            "execution_time_ms": result.execution_time_ms,
        }
        return response, metadata

    async def _handle_refresh_inbox(
        self, intent: IntentMatch, db: Session, context: Optional[Dict[str, Any]]
    ) -> Tuple[str, Dict[str, Any]]:
        orchestrator = self._get_orchestrator()
        items = self._load_recent_items(db, limit=25)

        if not items:
            raise ChatServiceError("I don't have any inbox items to triage yet.")

        agent_context = orchestrator.build_context(intent="refresh_inbox", items=items, user_id="default_user")
        result = await orchestrator.run("refresh_inbox", agent_context)
        response = self._format_refresh_summary(result)

        metadata = {
            "intent": "refresh_inbox",
            "function_call": True,
            "result": self._serialize_orchestration_result(result),
        }
        return response, metadata

    async def _handle_pending_actions(
        self, intent: IntentMatch, db: Session, context: Optional[Dict[str, Any]]
    ) -> Tuple[str, Dict[str, Any]]:
        pending_actions = (
            db.query(ActionProposal)
            .filter(ActionProposal.status == "pending")
            .order_by(ActionProposal.created_at.desc())
            .limit(6)
            .all()
        )

        if not pending_actions:
            return (
                "You're all caught up—there are no pending actions waiting for review.",
                {"intent": "pending_actions", "function_call": True, "actions": []},
            )

        lines = ["Here are the latest actions waiting for your approval:"]
        serialized_actions = []
        for idx, action in enumerate(pending_actions, start=1):
            title = action.explanation or action.action_type.replace("_", " ").title()
            lines.append(f"{idx}. {title} (risk: {action.risk_level})")
            serialized_actions.append(
                {
                    "id": str(action.id),
                    "agent_name": action.agent_name,
                    "action_type": action.action_type,
                    "risk_level": action.risk_level,
                    "explanation": action.explanation,
                }
            )

        metadata = {
            "intent": "pending_actions",
            "function_call": True,
            "actions": serialized_actions,
            "count": len(serialized_actions),
        }
        return "\n".join(lines), metadata

    async def _handle_help(self, intent: IntentMatch, db: Session, context: Optional[Dict[str, Any]]):
        message = (
            "You can ask me to plan your day, refresh/triage the inbox, or list pending actions. "
            "Try things like “plan my day”, “refresh the inbox”, or “what needs my approval?”."
        )
        return message, {"intent": "help"}

    async def _handle_general(
        self, user_message: str, intent: IntentMatch, db: Session, context: Optional[Dict[str, Any]] = None
    ):
        """Handle general queries using RAG + LLM for intelligent responses."""
        try:
            llm_client = LLMClient()

            # Try to get context from RAG using the shared vectorstore
            rag_context = ""
            sources = []
            try:
                from backend.api.routes.rag import _get_vectorstore, RAG_AVAILABLE

                if RAG_AVAILABLE:
                    vectorstore = _get_vectorstore()
                    docs = vectorstore.similarity_search(user_message, k=3)
                    if docs:
                        rag_context = "\n\n".join([doc.page_content for doc in docs])
                        sources = [doc.metadata.get("source", "knowledge_base") for doc in docs]
                        logger.info(f"RAG retrieved {len(docs)} docs for query")
            except Exception as e:
                logger.debug(f"RAG retrieval skipped: {e}")

            # Build context-aware prompt
            if rag_context:
                system_context = (
                    "You are a helpful AI assistant. Answer based on the provided context. "
                    "If the context doesn't contain relevant info, say so and provide general guidance."
                )
                prompt = f"{system_context}\n\nContext:\n{rag_context}\n\nUser question: {user_message}\n\nAnswer:"
            else:
                system_context = (
                    "You are a helpful AI assistant for a personal productivity system. "
                    "You can help with planning, inbox management, answering questions, "
                    "and general assistance. Be concise, helpful, and friendly."
                )
                prompt = f"{system_context}\n\nUser question: {user_message}\n\nProvide a helpful response:"

            response = llm_client.call(prompt, temperature=0.7, max_tokens=500)

            metadata = {"intent": "general", "llm_response": True}
            if sources:
                metadata["rag_sources"] = sources

            return response.strip(), metadata
        except Exception as exc:
            logger.warning("LLM general query failed, falling back to default: %s", exc)
            message = (
                "I'm ready to assist. Ask me to plan your day, refresh the inbox, or show pending actions "
                "whenever you need to run the agents."
            )
            return message, {"intent": intent.intent, "reason": intent.reason}

    def _get_orchestrator(self) -> Orchestrator:
        if self._orchestrator is None:
            try:
                self._orchestrator = Orchestrator()
            except ValueError as exc:
                raise ChatServiceError(
                    "The AI provider isn't configured. Set your API key in the backend configuration."
                ) from exc
        return self._orchestrator

    def _load_recent_items(self, db: Session, limit: int) -> List[Dict[str, Any]]:
        items = db.query(Item).order_by(Item.created_at.desc()).limit(limit).all()

        payload = []
        for item in items:
            metadata = item.agent_metadata
            payload.append(
                {
                    "id": str(item.id),
                    "title": item.title or "",
                    "body_preview": item.body_preview or "",
                    "body_full": item.body_full or "",
                    "source_type": item.source_type or "email",
                    "importance": getattr(metadata, "importance", "medium") if metadata else "medium",
                    "category": getattr(metadata, "category", "other") if metadata else "other",
                    "due_datetime": metadata.due_datetime.isoformat()
                    if (metadata and metadata.due_datetime)
                    else None,
                }
            )
        return payload

    def _format_plan_summary(self, plan: Dict[str, Any]) -> str:
        must_do = plan.get("must_do_today", [])
        focus = plan.get("focus_areas", [])
        recommendations = plan.get("time_recommendations", [])

        lines = ["Here's the plan the agents put together:"]

        if must_do:
            must_do_list = ", ".join(must_do[:5])
            lines.append(f"- Must-do items: {must_do_list}")

        if focus:
            focus_list = ", ".join(focus[:3])
            lines.append(f"- Focus areas: {focus_list}")

        if recommendations:
            top_blocks = []
            for rec in recommendations[:3]:
                task_name = rec.get("task", "Work block")
                suggested_time = rec.get("suggested_time", "TBD")
                duration = rec.get("duration_minutes", 60)
                top_blocks.append(f"{task_name} at {suggested_time} ({duration} min)")
            lines.append("- Suggested time blocks: " + "; ".join(top_blocks))

        if len(lines) == 1:
            lines.append("The planner agent ran but didn't produce detailed suggestions.")

        return "\n".join(lines)

    def _format_refresh_summary(self, result: OrchestrationResult) -> str:
        if not result.results:
            return "I ran the refresh workflow, but no agents returned any updates."

        lines = ["Refresh complete:"]
        for agent_name, agent_result in result.results.items():
            summary = agent_result.output_summary or {}
            summary_bits = [f"{key.replace('_', ' ')}: {value}" for key, value in summary.items()]
            if summary_bits:
                lines.append(f"- {agent_name.title()}: " + ", ".join(summary_bits))
            else:
                lines.append(f"- {agent_name.title()}: completed with status {agent_result.status}")

        return "\n".join(lines)

    def _serialize_orchestration_result(self, result: OrchestrationResult) -> Dict[str, Any]:
        serialized = {"status": result.status, "execution_time_ms": result.execution_time_ms, "results": {}}
        for agent_name, agent_result in (result.results or {}).items():
            serialized["results"][agent_name] = {
                "status": agent_result.status,
                "output_summary": agent_result.output_summary,
                "duration_ms": agent_result.duration_ms,
                "error_message": agent_result.error_message,
            }
        return serialized


session_store = ChatSessionStore()
chat_service = ChatService()


def _serialize_record(record: ChatMessageEntry) -> ChatMessageDTO:
    return ChatMessageDTO(
        id=str(record.id),
        content=record.content,
        sender=record.sender,  # type: ignore[arg-type]
        timestamp=record.created_at or datetime.now(timezone.utc),
        metadata=record.message_metadata,
    )


@router.post("/message", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest, db: Session = Depends(get_db)):
    """Primary entrypoint for chat messages."""
    content = request.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    chat_session = session_store.get_or_create(db, request.session_id)
    session_id = str(chat_session.id)

    session_store.append_message(
        db,
        chat_session,
        "user",
        content,
        metadata={"context": request.context} if request.context else None,
    )

    try:
        reply_text, metadata = await chat_service.handle_message(content, db, request.context)
    except ChatServiceError as exc:
        logger.error("Chat service failed: %s", exc)
        reply_text = str(exc) or "I ran into a problem processing that request."
        metadata = {"intent": "error"}
    except Exception as exc:
        logger.exception("Unexpected chat failure: %s", exc)
        reply_text = "Something went wrong when talking to the agents. Please try again shortly."
        metadata = {"intent": "error"}

    assistant_record = session_store.append_message(db, chat_session, "assistant", reply_text, metadata)

    return SendMessageResponse(message=_serialize_record(assistant_record), session_id=session_id)


@router.post("/stream")
async def stream_chat(request: SendMessageRequest, db: Session = Depends(get_db)):
    """Stream chat responses, including agent thoughts."""
    content = request.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    chat_session = session_store.get_or_create(db, request.session_id)
    session_id = str(chat_session.id)

    # Record user message
    session_store.append_message(
        db,
        chat_session,
        "user",
        content,
        metadata={"context": request.context} if request.context else None,
    )

    # Inject model preference into context metadata if provided
    if request.context is None:
        request.context = {}

    if request.model_provider:
        request.context["model_provider"] = request.model_provider
    if request.model_name:
        request.context["model_name"] = request.model_name

    async def event_generator():
        full_response_text = ""
        try:
            # Yield session ID first so client knows it
            yield json.dumps({"type": "session_id", "session_id": session_id}) + "\n"

            async for event in chat_service.stream_message(content, db, request.context):
                yield json.dumps(event) + "\n"
                if event["type"] == "message":
                    full_response_text = event["content"]

            # Store assistant message in DB after stream completes
            if full_response_text:
                session_store.append_message(db, chat_session, "assistant", full_response_text, {"streamed": True})

        except Exception as exc:
            logger.exception("Streaming error: %s", exc)
            yield json.dumps({"type": "error", "error": str(exc)}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


@router.get("/sessions")
async def get_sessions(limit: int = 10, db: Session = Depends(get_db)):
    """List recent chat sessions."""
    # This is a simplified query - in a real app we'd group by session_id and get the latest message
    # or have a separate 'ChatSessions' table with metadata.
    # For now, assuming ChatSession table exists.
    sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).limit(limit).all()

    return [
        {
            "id": str(s.id),
            "created_at": s.created_at,
            "updated_at": s.updated_at,
            # Heuristic title: "Chat <date>" or potentially stored title if we add that column
            "title": f"Chat {s.created_at.strftime('%b %d, %H:%M')}",
        }
        for s in sessions
    ]


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
    db.commit()

    # In a real system with long-running checkpoints, we would now resume the graph thread.
    # For this stateless MVP, we just update the DB. The next user message will trigger a new run,
    # and the graph (if smart enough to check DB) would pick it up.
    # Since our graph is one-shot per request currently, the 'resume' part happens when the user
    # says "Ok I approved it, continue" or similar.
    #
    # To make it seamless, we could trigger a background run here, but we don't have the user's
    # websocket/stream open to push the result back!
    # So we just return success, and the frontend (optimistically) updates UI.

    return {"status": proposal.status}


@router.get("/history/{session_id}", response_model=List[ChatMessageDTO])
async def get_history(session_id: str, db: Session = Depends(get_db)):
    """Return stored chat history for a session."""
    session = session_store.get_session(db, session_id)
    if not session:
        return []

    records = session_store.list_messages(db, session)
    return [_serialize_record(record) for record in records]
