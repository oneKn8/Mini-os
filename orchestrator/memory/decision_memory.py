"""
Decision Memory for Loop Prevention

Tracks agent decisions, questions, and tool executions to prevent infinite loops.

Features:
- Question deduplication (semantic similarity)
- Tool execution tracking
- Decision loop detection
- Circuit breaker logic

Example problematic loops this prevents:
1. "Did I check calendar?" → checks → "Did I check calendar?" (loop)
2. search_emails → no results → search_emails again (loop)
3. Should I ask about X? → asks → Should I ask about X? (decision loop)
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class Decision:
    """A decision made by the agent."""
    decision_type: str  # "question", "tool_execution", "action"
    content: str  # The question/tool/action
    context: str  # Context when decision was made
    timestamp: float = field(default_factory=time.time)
    result: Optional[Any] = None


class DecisionMemory:
    """
    Tracks agent decisions to prevent loops.

    Loop prevention strategies:
    1. Exact match - same question/tool already executed
    2. Semantic similarity - similar question already asked
    3. Frequency limit - same decision type repeated too often
    4. Circuit breaker - stop after N failed attempts
    """

    def __init__(
        self,
        max_same_question: int = 1,
        max_same_tool: int = 2,
        max_failed_attempts: int = 3,
        similarity_threshold: float = 0.85,
        enable_semantic_check: bool = True,
    ):
        """
        Initialize decision memory.

        Args:
            max_same_question: Max times to ask same/similar question
            max_same_tool: Max times to call same tool with same args
            max_failed_attempts: Max failed attempts before circuit breaker
            similarity_threshold: Similarity threshold for duplicate questions
            enable_semantic_check: Whether to use semantic similarity
        """
        self.max_same_question = max_same_question
        self.max_same_tool = max_same_tool
        self.max_failed_attempts = max_failed_attempts
        self.similarity_threshold = similarity_threshold
        self.enable_semantic_check = enable_semantic_check

        # Decision tracking
        self.questions_asked: List[Decision] = []
        self.tools_executed: List[Decision] = []
        self.actions_taken: List[Decision] = []

        # Failure tracking for circuit breaker
        self.failed_attempts: int = 0
        self.circuit_open: bool = False

        # Stats
        self.loops_prevented: int = 0

        # Lazy-loaded embedding model
        self._embedding_model = None

    def _get_embedding_model(self):
        """Lazy load embedding model for semantic similarity."""
        if not self.enable_semantic_check:
            return None

        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            except ImportError:
                logger.warning("sentence-transformers not installed, using exact matching only")
                self._embedding_model = None

        return self._embedding_model

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Compute semantic similarity between two texts."""
        model = self._get_embedding_model()
        if model is None:
            # Fallback to exact match
            return 1.0 if text1.lower().strip() == text2.lower().strip() else 0.0

        try:
            embeddings = model.encode([text1, text2])
            # Cosine similarity
            import numpy as np
            from numpy.linalg import norm
            cos_sim = np.dot(embeddings[0], embeddings[1]) / (norm(embeddings[0]) * norm(embeddings[1]))
            return float(cos_sim)
        except Exception as e:
            logger.error(f"Failed to compute similarity: {e}")
            return 0.0

    def has_asked(self, question: str, context: str = "") -> bool:
        """
        Check if similar question has been asked.

        Args:
            question: The question to check
            context: Current context

        Returns:
            True if similar question already asked
        """
        if self.circuit_open:
            return True

        # Check exact matches
        exact_matches = sum(
            1 for d in self.questions_asked
            if d.content.lower().strip() == question.lower().strip()
        )

        if exact_matches >= self.max_same_question:
            self.loops_prevented += 1
            logger.warning(f"Loop prevented: question asked {exact_matches} times: {question}")
            return True

        # Check semantic similarity
        if self.enable_semantic_check and self._get_embedding_model():
            for decision in self.questions_asked:
                similarity = self._compute_similarity(question, decision.content)
                if similarity >= self.similarity_threshold:
                    self.loops_prevented += 1
                    logger.warning(
                        f"Loop prevented: similar question (sim={similarity:.2f}): "
                        f"'{question}' ~= '{decision.content}'"
                    )
                    return True

        return False

    def record_question(self, question: str, context: str = "", result: Any = None):
        """
        Record a question that was asked.

        Args:
            question: The question
            context: Context when asked
            result: Result of asking
        """
        decision = Decision(
            decision_type="question",
            content=question,
            context=context,
            result=result,
        )
        self.questions_asked.append(decision)

        # Track failures for circuit breaker
        if result is None or (isinstance(result, dict) and result.get("error")):
            self.failed_attempts += 1
            if self.failed_attempts >= self.max_failed_attempts:
                self.circuit_open = True
                logger.error(
                    f"Circuit breaker opened after {self.failed_attempts} failed attempts"
                )
        else:
            # Reset on success
            self.failed_attempts = max(0, self.failed_attempts - 1)

    def has_executed_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        context: str = "",
    ) -> bool:
        """
        Check if tool has been executed with same arguments.

        Args:
            tool_name: Name of the tool
            args: Tool arguments
            context: Current context

        Returns:
            True if tool already executed with same args
        """
        if self.circuit_open:
            return True

        # Normalize args for comparison
        args_str = str(sorted(args.items())) if args else ""

        executions = sum(
            1 for d in self.tools_executed
            if d.content == tool_name and d.context == args_str
        )

        if executions >= self.max_same_tool:
            self.loops_prevented += 1
            logger.warning(
                f"Loop prevented: tool executed {executions} times: {tool_name}({args_str})"
            )
            return True

        return False

    def record_tool_execution(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any = None,
    ):
        """
        Record a tool execution.

        Args:
            tool_name: Name of the tool
            args: Tool arguments
            result: Execution result
        """
        args_str = str(sorted(args.items())) if args else ""

        decision = Decision(
            decision_type="tool_execution",
            content=tool_name,
            context=args_str,
            result=result,
        )
        self.tools_executed.append(decision)

        # Track failures
        if result is None or (isinstance(result, dict) and result.get("error")):
            self.failed_attempts += 1
            if self.failed_attempts >= self.max_failed_attempts:
                self.circuit_open = True
                logger.error(
                    f"Circuit breaker opened after {self.failed_attempts} failed tool executions"
                )
        else:
            self.failed_attempts = max(0, self.failed_attempts - 1)

    def is_looping(self, window_size: int = 5) -> bool:
        """
        Check if agent is in a decision loop.

        A loop is detected if:
        1. Same decision repeated in recent window
        2. Alternating pattern (A→B→A→B)

        Args:
            window_size: Number of recent decisions to check

        Returns:
            True if looping detected
        """
        all_decisions = (
            self.questions_asked[-window_size:]
            + self.tools_executed[-window_size:]
            + self.actions_taken[-window_size:]
        )

        if len(all_decisions) < 3:
            return False

        # Sort by timestamp
        all_decisions.sort(key=lambda d: d.timestamp)

        # Check for repeating pattern
        recent = [f"{d.decision_type}:{d.content}" for d in all_decisions[-window_size:]]

        # Simple loop detection: last 2 decisions repeated
        if len(recent) >= 4:
            if recent[-2:] == recent[-4:-2]:
                self.loops_prevented += 1
                logger.warning(f"Loop detected: repeating pattern {recent[-2:]}")
                return True

        # Alternating pattern
        if len(recent) >= 4:
            if recent[-1] == recent[-3] and recent[-2] == recent[-4]:
                self.loops_prevented += 1
                logger.warning(f"Loop detected: alternating pattern {recent[-4:]}")
                return True

        return False

    def should_early_exit(self) -> bool:
        """
        Check if agent should exit early due to circuit breaker.

        Returns:
            True if circuit breaker is open
        """
        return self.circuit_open

    def reset_circuit_breaker(self):
        """Reset circuit breaker."""
        self.circuit_open = False
        self.failed_attempts = 0
        logger.info("Circuit breaker reset")

    def clear(self):
        """Clear all decision history."""
        self.questions_asked.clear()
        self.tools_executed.clear()
        self.actions_taken.clear()
        self.failed_attempts = 0
        self.circuit_open = False
        self.loops_prevented = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "questions_asked": len(self.questions_asked),
            "tools_executed": len(self.tools_executed),
            "actions_taken": len(self.actions_taken),
            "failed_attempts": self.failed_attempts,
            "circuit_open": self.circuit_open,
            "loops_prevented": self.loops_prevented,
        }

    def get_recent_decisions(self, count: int = 10) -> List[Decision]:
        """
        Get recent decisions across all types.

        Args:
            count: Number of recent decisions to return

        Returns:
            List of recent decisions sorted by timestamp
        """
        all_decisions = (
            self.questions_asked + self.tools_executed + self.actions_taken
        )
        all_decisions.sort(key=lambda d: d.timestamp, reverse=True)
        return all_decisions[:count]

    def __repr__(self) -> str:
        stats = self.get_stats()
        return (
            f"DecisionMemory(questions={stats['questions_asked']}, "
            f"tools={stats['tools_executed']}, "
            f"loops_prevented={stats['loops_prevented']}, "
            f"circuit_open={stats['circuit_open']})"
        )
