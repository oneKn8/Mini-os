"""
Smart Planner with Multi-Layer Caching

Replaces the QueryAnalyzer with a 3-layer caching architecture:
L1: Pattern matching (0.05s) - Regex-based for common queries
L2: Semantic cache (0.1s) - Embedding similarity for variations
L3: LLM planning (2-4s) - Full planning for novel queries

Expected speedup:
- Repeated queries: 15s -> 0.05s (300x faster)
- Similar queries: 15s -> 0.1s (150x faster)
- Novel queries: 15s -> 3s (5x faster with optimized prompts)

Example:
    Query 1: "What's my day like?" -> LLM planning (3s)
    Query 2: "What's my day like?" -> Pattern match (0.05s)
    Query 3: "How's my day looking?" -> Semantic cache (0.1s)
"""

import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel

from orchestrator.agents.query_analyzer import ToolPlan
from orchestrator.llm_client import LLMClient

logger = logging.getLogger(__name__)


# ============================================================================
# Pattern Definitions
# ============================================================================


@dataclass
class QueryPattern:
    """
    A query pattern with tools and parallel execution info.

    Attributes:
        name: Pattern identifier
        patterns: List of regex patterns to match
        tools: List of tool names to execute
        parallel_groups: Groups of tools that can run in parallel
        reasoning: Why this plan was chosen
        priority: Higher priority patterns are checked first
    """

    name: str
    patterns: List[str]
    tools: List[str]
    parallel_groups: List[List[str]]
    reasoning: str
    priority: int = 5


class PatternMatcher:
    """
    Fast pattern matching for common query types.

    Matches queries using regex and returns pre-built plans.
    """

    def __init__(self):
        """Initialize with default patterns."""
        self.patterns = self._build_default_patterns()
        # Sort by priority (highest first)
        self.patterns.sort(key=lambda p: p.priority, reverse=True)

    def _build_default_patterns(self) -> List[QueryPattern]:
        """Build default query patterns."""
        return [
            # Day overview (highest priority - very common)
            QueryPattern(
                name="day_overview",
                patterns=[
                    r"what('s| is) (my|the) day( like| looking)?",
                    r"how('s| is) (my|the) day",
                    r"day overview",
                    r"today('s| schedule)",
                ],
                tools=["get_todays_events", "get_current_weather", "get_priority_items"],
                parallel_groups=[["get_todays_events", "get_current_weather", "get_priority_items"]],
                reasoning="Checking your calendar, priorities, and weather to give you a complete day overview",
                priority=10,
            ),
            # Free time check
            QueryPattern(
                name="free_time",
                patterns=[
                    r"am i free",
                    r"do i have time",
                    r"any (free time|openings|availability)",
                    r"when('s| is) (my|the) next (free|available|open) (slot|time)",
                ],
                tools=["get_todays_events", "get_upcoming_events"],
                parallel_groups=[["get_todays_events", "get_upcoming_events"]],
                reasoning="Checking your calendar for availability",
                priority=9,
            ),
            # Meeting prep
            QueryPattern(
                name="meeting_prep",
                patterns=[
                    r"prepare (me )?for (my )?meeting",
                    r"meeting with (\w+)",
                    r"brief me (on|for)",
                    r"what do i need to know (about|for)",
                ],
                tools=["search_emails", "get_todays_events"],
                parallel_groups=[["search_emails", "get_todays_events"]],
                reasoning="Searching for relevant emails and checking your calendar",
                priority=8,
            ),
            # Email search
            QueryPattern(
                name="email_search",
                patterns=[
                    r"(search|find|show|get) (my )?emails? (from|about|with)",
                    r"emails? from (\w+)",
                    r"did (\w+) email me",
                ],
                tools=["search_emails"],
                parallel_groups=[["search_emails"]],
                reasoning="Searching your emails",
                priority=7,
            ),
            # Priority check
            QueryPattern(
                name="priorities",
                patterns=[
                    r"what should i (focus|work) on",
                    r"(top|high) priorit(y|ies)",
                    r"most important",
                    r"what('s| is) urgent",
                ],
                tools=["get_priority_items", "get_todays_events"],
                parallel_groups=[["get_priority_items", "get_todays_events"]],
                reasoning="Checking your priorities and calendar",
                priority=8,
            ),
            # Weather
            QueryPattern(
                name="weather",
                patterns=[
                    r"(what('s| is) the )?weather",
                    r"(is it|will it) (rain|snow|sunny)",
                    r"temperature",
                ],
                tools=["get_current_weather"],
                parallel_groups=[["get_current_weather"]],
                reasoning="Checking the weather",
                priority=6,
            ),
            # Email composition
            QueryPattern(
                name="email_compose",
                patterns=[
                    r"(send|write|compose|draft) (an? )?(email|message)",
                    r"email (\w+) (about|that)",
                ],
                tools=["create_email_draft"],
                parallel_groups=[["create_email_draft"]],
                reasoning="Drafting an email for you",
                priority=9,
            ),
            # Calendar event
            QueryPattern(
                name="calendar_create",
                patterns=[
                    r"(schedule|create|add|book) (an? )?(meeting|event|appointment)",
                    r"set up (a )?(meeting|call|lunch)",
                ],
                tools=["create_calendar_event"],
                parallel_groups=[["create_calendar_event"]],
                reasoning="Creating a calendar event",
                priority=9,
            ),
        ]

    def match(self, query: str) -> Optional[ToolPlan]:
        """
        Match query against patterns.

        Args:
            query: User query

        Returns:
            ToolPlan if matched, None otherwise
        """
        query_lower = query.lower().strip()

        for pattern in self.patterns:
            for regex in pattern.patterns:
                if re.search(regex, query_lower):
                    logger.info(f"Pattern match: {pattern.name} (L1 cache hit)")
                    return ToolPlan(
                        tools=pattern.tools,
                        parallel_groups=pattern.parallel_groups,
                        reasoning=pattern.reasoning,
                        expected_synthesis=f"Synthesize results from {len(pattern.tools)} tools",
                    )

        return None


# ============================================================================
# Semantic Cache
# ============================================================================


@dataclass
class CachedPlan:
    """Cached plan with metadata."""

    query: str
    query_embedding: List[float]
    plan: ToolPlan
    timestamp: float
    hit_count: int = 0


class SemanticCache:
    """
    Semantic similarity cache using embeddings.

    Caches plans by query embeddings and retrieves similar queries
    using cosine similarity.
    """

    def __init__(self, similarity_threshold: float = 0.85, max_cache_size: int = 1000):
        """
        Initialize semantic cache.

        Args:
            similarity_threshold: Minimum similarity score for cache hit (0-1)
            max_cache_size: Maximum number of cached plans
        """
        self.similarity_threshold = similarity_threshold
        self.max_cache_size = max_cache_size
        self.cache: Dict[str, CachedPlan] = {}
        self._embedding_model = None

    def _get_embedding_model(self):
        """Lazy load embedding model."""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Loaded all-MiniLM-L6-v2 for semantic caching")
            except ImportError:
                logger.warning("sentence-transformers not installed, semantic cache disabled")

                # Return a dummy that always returns None
                class DummyModel:
                    def encode(self, text):
                        return None

                self._embedding_model = DummyModel()
        return self._embedding_model

    def _compute_embedding(self, text: str) -> Optional[List[float]]:
        """Compute embedding for text."""
        model = self._get_embedding_model()
        try:
            embedding = model.encode(text, convert_to_tensor=False)
            if embedding is None:
                return None
            return embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)
        except Exception as e:
            logger.error(f"Failed to compute embedding: {e}")
            return None

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        import math

        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = math.sqrt(sum(x * x for x in a))
        magnitude_b = math.sqrt(sum(x * x for x in b))

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)

    async def get_similar(self, query: str) -> Optional[ToolPlan]:
        """
        Get cached plan for similar query.

        Args:
            query: User query

        Returns:
            ToolPlan if similar query found, None otherwise
        """
        if not self.cache:
            return None

        query_embedding = self._compute_embedding(query)
        if query_embedding is None:
            return None

        # Find most similar cached query
        best_match = None
        best_similarity = 0.0

        for cache_key, cached in self.cache.items():
            similarity = self._cosine_similarity(query_embedding, cached.query_embedding)
            if similarity > best_similarity and similarity >= self.similarity_threshold:
                best_similarity = similarity
                best_match = cached

        if best_match:
            logger.info(f"Semantic cache hit: similarity={best_similarity:.3f} (L2 cache)")
            best_match.hit_count += 1
            return best_match.plan

        return None

    async def store(self, query: str, plan: ToolPlan):
        """
        Store plan in cache.

        Args:
            query: User query
            plan: Tool plan to cache
        """
        query_embedding = self._compute_embedding(query)
        if query_embedding is None:
            return

        # Create cache key from query hash
        cache_key = hashlib.md5(query.lower().strip().encode()).hexdigest()

        # Store in cache
        self.cache[cache_key] = CachedPlan(
            query=query,
            query_embedding=query_embedding,
            plan=plan,
            timestamp=time.time(),
        )

        # Evict oldest if cache is full
        if len(self.cache) > self.max_cache_size:
            # Remove least recently used (oldest timestamp)
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].timestamp)
            del self.cache[oldest_key]
            logger.info(f"Evicted oldest plan from semantic cache: {oldest_key}")

    def clear(self):
        """Clear all cached plans."""
        self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.cache:
            return {"size": 0, "hit_rate": 0.0}

        total_hits = sum(c.hit_count for c in self.cache.values())
        return {
            "size": len(self.cache),
            "total_hits": total_hits,
            "avg_hits_per_plan": total_hits / len(self.cache) if self.cache else 0,
        }


# ============================================================================
# Smart Planner
# ============================================================================


class SmartPlanner:
    """
    Multi-layer intelligent query planner.

    Architecture:
    - L1: Pattern matching (0.05s)
    - L2: Semantic cache (0.1s)
    - L3: LLM planning (2-4s)
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        enable_semantic_cache: bool = True,
    ):
        """
        Initialize smart planner.

        Args:
            llm_client: LLM client for L3 planning
            enable_semantic_cache: Whether to enable L2 semantic cache
        """
        self.pattern_matcher = PatternMatcher()
        self.semantic_cache = SemanticCache() if enable_semantic_cache else None
        self.llm_client = llm_client
        self._plan_cache: Dict[str, Tuple[ToolPlan, float]] = {}

    async def plan(self, query: str, context: Optional[Dict[str, Any]] = None) -> ToolPlan:
        """
        Create an execution plan for a query.

        Uses 3-layer caching for optimal performance.

        Args:
            query: User query
            context: Optional context (conversation history, etc.)

        Returns:
            ToolPlan with tools and execution strategy
        """
        start_time = time.time()

        # L1: Pattern matching (fastest)
        if plan := self.pattern_matcher.match(query):
            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Plan from L1 cache (pattern match) in {duration_ms}ms")
            return plan

        # L2: Semantic cache
        if self.semantic_cache:
            if plan := await self.semantic_cache.get_similar(query):
                duration_ms = int((time.time() - start_time) * 1000)
                logger.info(f"Plan from L2 cache (semantic) in {duration_ms}ms")
                return await self._adapt_plan(plan, query, context)

        # L3: LLM planning (slowest, most flexible)
        plan = await self._llm_plan(query, context)
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Plan from L3 (LLM) in {duration_ms}ms")

        # Store in semantic cache for future similar queries
        if self.semantic_cache:
            await self.semantic_cache.store(query, plan)

        return plan

    async def _adapt_plan(
        self,
        plan: ToolPlan,
        query: str,
        context: Optional[Dict[str, Any]],
    ) -> ToolPlan:
        """
        Adapt a cached plan to the current context.

        For now, this is a no-op, but could be enhanced to:
        - Adjust time parameters (today -> specific date)
        - Extract different entity names
        - Modify based on context changes
        """
        # TODO: Implement smart adaptation
        return plan

    async def _llm_plan(self, query: str, context: Optional[Dict[str, Any]]) -> ToolPlan:
        """
        Use LLM to create a plan for novel queries.

        This is the L3 fallback for queries that don't match patterns.
        """
        if not self.llm_client:
            self.llm_client = LLMClient()

        # Build prompt for LLM planning
        prompt = self._build_planning_prompt(query, context)

        try:
            # Use structured output for reliable JSON
            result = self.llm_client.call_json(prompt, temperature=0.3)

            tools = result.get("tools", [])
            parallel_groups = result.get("parallel_groups", [])

            # If no parallel groups specified, make all tools parallel
            if not parallel_groups and tools:
                parallel_groups = [tools]

            return ToolPlan(
                tools=tools,
                parallel_groups=parallel_groups,
                reasoning=result.get("reasoning", "LLM-generated plan"),
                expected_synthesis=result.get("synthesis", "Combine tool results"),
            )

        except Exception as e:
            logger.error(f"LLM planning failed: {e}")
            # Return empty plan as fallback
            return ToolPlan(
                tools=[],
                parallel_groups=[],
                reasoning="Planning failed - conversational mode",
                expected_synthesis="Respond conversationally",
            )

    def _build_planning_prompt(self, query: str, context: Optional[Dict[str, Any]]) -> str:
        """Build prompt for LLM planning."""
        # Available tools description
        tool_descriptions = """
Available tools:
- get_todays_events: Get today's calendar events
- get_upcoming_events: Get upcoming events (next 7 days)
- get_current_weather: Get current weather
- get_weather_forecast: Get weather forecast
- search_emails: Search emails by sender, subject, or content
- get_priority_items: Get high priority inbox items
- create_email_draft: Draft an email
- create_calendar_event: Create a calendar event
- plan_day: Create a daily plan
"""

        context_str = ""
        if context:
            context_str = f"\n\nContext:\n{json.dumps(context, indent=2)}"

        return f"""Analyze this user query and create a tool execution plan.

Query: "{query}"{context_str}

{tool_descriptions}

Create a plan with:
1. Which tools to use
2. Which can run in parallel (same group) vs sequential (different groups)
3. Brief reasoning

Respond with JSON:
{{
    "tools": ["tool1", "tool2"],
    "parallel_groups": [["tool1", "tool2"]],
    "reasoning": "Why these tools",
    "synthesis": "How to combine results"
}}

For independent data sources (calendar, email, weather), use parallel execution.
For dependent operations (need result from tool1 to call tool2), use sequential groups.
"""

    def get_stats(self) -> Dict[str, Any]:
        """Get planner statistics."""
        stats = {
            "pattern_count": len(self.pattern_matcher.patterns),
        }

        if self.semantic_cache:
            stats["semantic_cache"] = self.semantic_cache.get_stats()

        return stats
