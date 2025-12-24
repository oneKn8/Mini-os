"""
Smart Compactor - LLM-based conversation summarization.

Uses LLM to create intelligent summaries of old conversation history.
Preserves key information while dramatically reducing tokens.

Example:
    40 messages (80K tokens) -> 1 summary (2K tokens) = 40x compression
"""

import logging
from typing import List, Optional

from orchestrator.context.context_window_manager import MessageEntry

logger = logging.getLogger(__name__)


class SmartCompactor:
    """
    LLM-powered conversation compactor.

    Creates intelligent summaries that preserve:
    - User's goals and intents
    - Key decisions made
    - Important context for future queries
    - Action items and outcomes
    """

    def __init__(self, llm_client=None):
        """
        Initialize smart compactor.

        Args:
            llm_client: LLM client for summarization (optional)
        """
        self.llm_client = llm_client
        self._summary_cache = {}

    async def compact_messages(
        self,
        messages: List[MessageEntry],
        target_tokens: Optional[int] = None,
    ) -> str:
        """
        Compact messages into intelligent summary.

        Args:
            messages: Messages to compact
            target_tokens: Target summary size (default: ~2000)

        Returns:
            Compact summary preserving key information
        """
        if not messages:
            return "[Empty conversation]"

        target_tokens = target_tokens or 2000

        # If LLM available, use it for intelligent summarization
        if self.llm_client:
            return await self._llm_summarize(messages, target_tokens)

        # Fallback: rule-based summarization
        return self._rule_based_summarize(messages, target_tokens)

    async def _llm_summarize(
        self,
        messages: List[MessageEntry],
        target_tokens: int,
    ) -> str:
        """Use LLM to create intelligent summary."""
        # Build conversation text
        conversation = self._format_messages(messages)

        # Create summarization prompt
        prompt = f"""Summarize this conversation concisely, preserving key information:

{conversation}

Create a summary that:
1. Captures user's main goals and questions
2. Lists key decisions or actions taken
3. Preserves important context for future queries
4. Is under {target_tokens} tokens

Format as:
[Conversation Summary]
- User goals: ...
- Topics discussed: ...
- Key outcomes: ...
- Context to remember: ...

Summary:"""

        try:
            # Use LLM to summarize (fast model, low temperature)
            summary = await self.llm_client.acall(
                prompt,
                temperature=0.3,
                max_tokens=target_tokens,
            )

            logger.info(f"LLM summarized {len(messages)} messages " f"(target: {target_tokens} tokens)")

            return summary

        except Exception as e:
            logger.error(f"LLM summarization failed: {e}, using fallback")
            return self._rule_based_summarize(messages, target_tokens)

    def _rule_based_summarize(
        self,
        messages: List[MessageEntry],
        target_tokens: int,
    ) -> str:
        """Fallback: rule-based summarization."""
        # Extract key components
        user_messages = [m for m in messages if m.role == "user"]
        assistant_messages = [m for m in messages if m.role == "assistant"]

        # Get topics and intents
        topics = self._extract_topics(user_messages)
        actions = self._extract_actions(assistant_messages)

        # Build structured summary
        summary_parts = [
            f"[Summary: {len(messages)} messages from previous conversation]",
            "",
            f"**User discussed:**",
        ]

        # Add topics
        for i, topic in enumerate(topics[:5], 1):
            summary_parts.append(f"  {i}. {topic}")

        # Add actions/outcomes
        if actions:
            summary_parts.append("")
            summary_parts.append("**Actions taken:**")
            for i, action in enumerate(actions[:3], 1):
                summary_parts.append(f"  {i}. {action}")

        # Add sample recent exchanges
        recent_sample = user_messages[-3:] if len(user_messages) > 3 else user_messages
        if recent_sample:
            summary_parts.append("")
            summary_parts.append("**Recent queries:**")
            for msg in recent_sample:
                preview = self._extract_preview(msg.content, 80)
                summary_parts.append(f"  - {preview}")

        summary = "\n".join(summary_parts)

        # Truncate if needed
        if len(summary) > target_tokens * 4:  # Rough char estimate
            summary = summary[: target_tokens * 4] + "..."

        return summary

    def _format_messages(self, messages: List[MessageEntry]) -> str:
        """Format messages for LLM input."""
        formatted = []
        for msg in messages:
            role = msg.role.capitalize()
            formatted.append(f"{role}: {msg.content}")

        return "\n\n".join(formatted)

    def _extract_topics(self, user_messages: List[MessageEntry]) -> List[str]:
        """Extract main topics from user messages."""
        topics = []

        for msg in user_messages:
            # Extract first question or sentence
            content = msg.content
            sentences = content.split(".")
            if sentences:
                topic = sentences[0].strip()
                if len(topic) > 10 and len(topic) < 100:
                    topics.append(topic)

        return topics

    def _extract_actions(self, assistant_messages: List[MessageEntry]) -> List[str]:
        """Extract actions from assistant messages."""
        actions = []

        # Look for action indicators
        action_keywords = [
            "created",
            "drafted",
            "scheduled",
            "sent",
            "updated",
            "found",
            "searched",
            "analyzed",
            "checked",
        ]

        for msg in assistant_messages:
            content_lower = msg.content.lower()
            for keyword in action_keywords:
                if keyword in content_lower:
                    # Extract sentence containing action
                    sentences = msg.content.split(".")
                    for sentence in sentences:
                        if keyword in sentence.lower():
                            action = sentence.strip()
                            if 10 < len(action) < 100:
                                actions.append(action)
                                break
                    break

        return list(set(actions))  # Remove duplicates

    def _extract_preview(self, text: str, max_chars: int) -> str:
        """Extract preview of text."""
        # Remove newlines
        text = text.replace("\n", " ").strip()

        if len(text) <= max_chars:
            return text

        # Find last space before limit
        truncated = text[:max_chars]
        last_space = truncated.rfind(" ")

        if last_space > max_chars * 0.8:  # At least 80% of desired length
            return truncated[:last_space] + "..."

        return truncated + "..."
