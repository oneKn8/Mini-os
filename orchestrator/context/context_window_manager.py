"""
Context Window Manager with Auto-Compaction

Manages conversation context with intelligent compaction when approaching limits.
Mimics Claude Code's behavior - seamless compaction without user interruption.

Strategy:
- 126K token limit (Claude 3.5 Sonnet / GPT-4 Turbo)
- Auto-compact at 100K (80% threshold)
- Keep last 10 messages verbatim (recent context critical)
- Compress older messages into summaries
- New chat = fresh 126K available

Example:
    User has 50-message conversation (110K tokens)
    -> Auto-compact triggered
    -> Keep: Last 10 messages verbatim (5K tokens)
    -> Compress: Messages 1-40 into summary (2K tokens)
    -> Result: 95K -> 7K tokens, ready for next 119K
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import tiktoken

logger = logging.getLogger(__name__)


@dataclass
class MessageEntry:
    """A single conversation message with metadata."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)
    tokens: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationSession:
    """Tracks context for a single conversation session."""

    session_id: str
    messages: List[MessageEntry] = field(default_factory=list)
    total_tokens: int = 0
    compaction_count: int = 0
    created_at: float = field(default_factory=time.time)
    last_compacted_at: Optional[float] = None


class ContextWindowManager:
    """
    Manages conversation context with automatic compaction.

    Features:
    - 126K token limit (context window size)
    - Auto-compact at 100K (80% threshold)
    - Keep recent messages verbatim
    - Compress old messages
    - Per-session tracking
    """

    def __init__(
        self,
        max_tokens: int = 126000,
        compact_threshold: float = 0.80,  # Compact at 80%
        keep_recent_messages: int = 10,  # Keep last N messages verbatim
        model: str = "gpt-4",
    ):
        """
        Initialize context window manager.

        Args:
            max_tokens: Maximum context window size
            compact_threshold: Trigger compaction at this % of max
            keep_recent_messages: Number of recent messages to keep verbatim
            model: Model name for token counting
        """
        self.max_tokens = max_tokens
        self.compact_threshold = compact_threshold
        self.compact_trigger = int(max_tokens * compact_threshold)
        self.keep_recent_messages = keep_recent_messages
        self.model = model

        # Token encoder
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except Exception:
            self.encoding = tiktoken.get_encoding("cl100k_base")  # Fallback

        # Session tracking
        self.sessions: Dict[str, ConversationSession] = {}

        # Stats
        self.stats = {
            "total_compactions": 0,
            "tokens_saved": 0,
            "sessions_created": 0,
        }

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        try:
            return len(self.encoding.encode(text))
        except Exception:
            # Fallback: rough estimate
            return len(text) // 4

    def get_or_create_session(self, session_id: str) -> ConversationSession:
        """Get existing session or create new one."""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationSession(session_id=session_id)
            self.stats["sessions_created"] += 1
            logger.info(f"Created new session: {session_id} (fresh 126K available)")

        return self.sessions[session_id]

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """
        Add message to session and check if compaction needed.

        Args:
            session_id: Session identifier
            role: "user" or "assistant"
            content: Message content
            metadata: Optional metadata

        Returns:
            True if compaction was triggered
        """
        session = self.get_or_create_session(session_id)

        # Count tokens
        tokens = self.count_tokens(content)

        # Create message entry
        message = MessageEntry(
            role=role,
            content=content,
            tokens=tokens,
            metadata=metadata or {},
        )

        session.messages.append(message)
        session.total_tokens += tokens

        logger.debug(f"Added message: {tokens} tokens " f"(total: {session.total_tokens}/{self.max_tokens})")

        # Check if compaction needed
        if session.total_tokens >= self.compact_trigger:
            logger.info(f"Compaction triggered: {session.total_tokens} tokens " f"(threshold: {self.compact_trigger})")
            self._compact_session(session)
            return True

        return False

    def _compact_session(self, session: ConversationSession):
        """
        Compact session by summarizing old messages.

        Strategy:
        1. Keep last N messages verbatim (recent context)
        2. Summarize older messages into compact summary
        3. Replace old messages with summary
        """
        if len(session.messages) <= self.keep_recent_messages:
            logger.debug("Session has few messages, skipping compaction")
            return

        # Split messages
        messages_to_compress = session.messages[: -self.keep_recent_messages]
        recent_messages = session.messages[-self.keep_recent_messages :]

        # Create summary of old messages
        summary_content = self._create_summary(messages_to_compress)
        summary_tokens = self.count_tokens(summary_content)

        # Calculate tokens before/after
        old_tokens = sum(m.tokens for m in messages_to_compress)
        tokens_saved = old_tokens - summary_tokens

        # Create summary message
        summary_message = MessageEntry(
            role="system",
            content=summary_content,
            tokens=summary_tokens,
            metadata={
                "is_summary": True,
                "original_messages": len(messages_to_compress),
                "original_tokens": old_tokens,
                "compacted_at": time.time(),
            },
        )

        # Replace old messages with summary
        session.messages = [summary_message] + recent_messages
        session.total_tokens = summary_tokens + sum(m.tokens for m in recent_messages)
        session.compaction_count += 1
        session.last_compacted_at = time.time()

        # Update stats
        self.stats["total_compactions"] += 1
        self.stats["tokens_saved"] += tokens_saved

        logger.info(
            f"Compacted session {session.session_id}: "
            f"{old_tokens} -> {summary_tokens} tokens "
            f"(saved {tokens_saved}, {len(messages_to_compress)} -> 1 message)"
        )

    def _create_summary(self, messages: List[MessageEntry]) -> str:
        """
        Create compact summary of message history.

        For now, uses simple extraction. In production, would use LLM.
        """
        # Group by role
        user_messages = [m.content for m in messages if m.role == "user"]
        assistant_messages = [m.content for m in messages if m.role == "assistant"]

        # Extract key topics (simple version)
        topics = self._extract_topics(user_messages)

        # Build summary
        summary_parts = [
            f"[Conversation Summary: {len(messages)} previous messages]",
            "",
            f"User discussed: {', '.join(topics[:5])}",
            f"Total exchanges: {len(user_messages)} questions, {len(assistant_messages)} responses",
        ]

        # Add sample of user intents
        if user_messages:
            sample = user_messages[-3:] if len(user_messages) > 3 else user_messages
            summary_parts.append("")
            summary_parts.append("Recent topics:")
            for i, msg in enumerate(sample, 1):
                # Extract first sentence or 100 chars
                preview = msg.split(".")[0][:100] if msg else ""
                summary_parts.append(f"  {i}. {preview}...")

        return "\n".join(summary_parts)

    def _extract_topics(self, messages: List[str]) -> List[str]:
        """Extract key topics from messages (simple keyword extraction)."""
        # In production, would use NER or LLM
        keywords = set()

        common_words = {
            "what",
            "how",
            "when",
            "where",
            "who",
            "can",
            "could",
            "would",
            "the",
            "is",
            "are",
            "my",
            "me",
            "you",
            "your",
            "this",
            "that",
        }

        for msg in messages:
            words = msg.lower().split()
            for word in words:
                word = word.strip(".,!?")
                if len(word) > 3 and word not in common_words:
                    keywords.add(word)

        return list(keywords)[:10]

    def get_context_for_llm(
        self,
        session_id: str,
        include_system: bool = True,
    ) -> List[Dict[str, str]]:
        """
        Get conversation history formatted for LLM.

        Args:
            session_id: Session identifier
            include_system: Whether to include system messages

        Returns:
            List of message dicts with role and content
        """
        session = self.get_or_create_session(session_id)

        messages = []
        for msg in session.messages:
            if not include_system and msg.role == "system":
                continue

            messages.append(
                {
                    "role": msg.role,
                    "content": msg.content,
                }
            )

        return messages

    def get_token_usage(self, session_id: str) -> Dict[str, Any]:
        """Get token usage stats for session."""
        session = self.get_or_create_session(session_id)

        return {
            "total_tokens": session.total_tokens,
            "max_tokens": self.max_tokens,
            "utilization": session.total_tokens / self.max_tokens,
            "available": self.max_tokens - session.total_tokens,
            "messages": len(session.messages),
            "compactions": session.compaction_count,
            "will_compact_at": self.compact_trigger,
        }

    def reset_session(self, session_id: str):
        """Reset session (new chat)."""
        if session_id in self.sessions:
            old_session = self.sessions[session_id]
            logger.info(
                f"Reset session {session_id}: "
                f"had {old_session.total_tokens} tokens, "
                f"{len(old_session.messages)} messages, "
                f"{old_session.compaction_count} compactions"
            )
            del self.sessions[session_id]

        # Will create fresh session on next add_message

    def get_stats(self) -> Dict[str, Any]:
        """Get global statistics."""
        return {
            **self.stats,
            "active_sessions": len(self.sessions),
            "max_tokens": self.max_tokens,
            "compact_threshold": f"{self.compact_threshold * 100:.0f}%",
        }

    def __repr__(self) -> str:
        return (
            f"ContextWindowManager("
            f"max={self.max_tokens}, "
            f"compact_at={self.compact_trigger}, "
            f"sessions={len(self.sessions)})"
        )
