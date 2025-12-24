"""
Query Analyzer - Intelligent multi-tool orchestration.

This module analyzes complex user queries and determines:
1. What the user is really asking for
2. Which tools are needed
3. In what order to call them
4. How to combine the results

Examples of multi-tool queries:
- "Am I free tomorrow?" -> calendar + weather (for outdoor plans) + emails (pending commitments)
- "Prepare me for my meeting with John" -> search emails from John + calendar context
- "What should I focus on?" -> priorities + calendar (meeting load) + weather (energy levels)
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

from orchestrator.llm_client import LLMClient

logger = logging.getLogger(__name__)


# ============================================================================
# Query Analysis Schemas
# ============================================================================


@dataclass
class ToolDependency:
    """Represents a tool and its dependencies."""

    tool_name: str
    required_before: List[str] = field(default_factory=list)  # Tools that must run first
    enhances: List[str] = field(default_factory=list)  # Tools that benefit from this result
    priority: int = 1  # Higher = more important


class QueryIntent(BaseModel):
    """Analyzed intent of a user query."""

    primary_intent: str = Field(description="Main thing the user wants")
    secondary_intents: List[str] = Field(default_factory=list, description="Additional related intents")
    entities: Dict[str, Any] = Field(
        default_factory=dict, description="Extracted entities (people, dates, projects, etc.)"
    )
    time_context: Optional[str] = Field(default=None, description="Time context: today, tomorrow, this week, etc.")
    requires_action: bool = Field(default=False, description="Whether this requires creating/modifying something")


class ToolPlan(BaseModel):
    """Plan for executing tools."""

    tools: List[str] = Field(description="Tools to execute in order")
    parallel_groups: List[List[str]] = Field(
        default_factory=list, description="Groups of tools that can run in parallel"
    )
    reasoning: str = Field(description="Why these tools were chosen")
    expected_synthesis: str = Field(description="How to combine the results")


# ============================================================================
# Tool Dependency Graph
# ============================================================================

TOOL_GRAPH = {
    # Planning tools
    "plan_day": ToolDependency(
        tool_name="plan_day",
        enhances=["get_todays_events", "get_current_weather"],
        priority=2,
    ),
    "get_priority_items": ToolDependency(
        tool_name="get_priority_items",
        enhances=["plan_day"],
        priority=2,
    ),
    # Calendar tools
    "get_todays_events": ToolDependency(
        tool_name="get_todays_events",
        enhances=["plan_day", "get_current_weather"],
        priority=1,
    ),
    "get_upcoming_events": ToolDependency(
        tool_name="get_upcoming_events",
        enhances=["get_weather_forecast"],
        priority=1,
    ),
    "create_calendar_event": ToolDependency(
        tool_name="create_calendar_event",
        required_before=["get_todays_events", "get_upcoming_events"],
        priority=3,
    ),
    "create_email_draft": ToolDependency(
        tool_name="create_email_draft",
        priority=3,
    ),
    # Weather tools
    "get_current_weather": ToolDependency(
        tool_name="get_current_weather",
        enhances=["plan_day"],
        priority=1,
    ),
    "get_weather_forecast": ToolDependency(
        tool_name="get_weather_forecast",
        enhances=["get_upcoming_events"],
        priority=1,
    ),
    # Email tools
    "search_emails": ToolDependency(
        tool_name="search_emails",
        priority=2,
    ),
    "get_recent_emails": ToolDependency(
        tool_name="get_recent_emails",
        enhances=["plan_day"],
        priority=1,
    ),
    "get_email_summary": ToolDependency(
        tool_name="get_email_summary",
        priority=1,
    ),
    # Knowledge tools
    "query_knowledge_base": ToolDependency(
        tool_name="query_knowledge_base",
        priority=1,
    ),
    # Action tools
    "get_pending_actions": ToolDependency(
        tool_name="get_pending_actions",
        priority=1,
    ),
}


# ============================================================================
# Query Patterns
# ============================================================================

QUERY_PATTERNS = {
    # Holistic queries that need multiple tools
    "day_overview": {
        "patterns": ["how's my day", "what's my day", "day looking", "today look", "schedule today"],
        "tools": ["get_todays_events", "get_current_weather", "get_priority_items"],
        "synthesis": "Combine calendar, weather, and priorities into a cohesive day overview",
    },
    "tomorrow_prep": {
        "patterns": ["tomorrow", "prepare for tomorrow", "ready for tomorrow"],
        "tools": ["get_upcoming_events", "get_weather_forecast", "search_emails"],
        "synthesis": "Preview tomorrow with events, weather, and related emails",
    },
    "week_overview": {
        "patterns": ["this week", "week ahead", "coming week", "next few days"],
        "tools": ["get_upcoming_events", "get_weather_forecast", "get_priority_items"],
        "synthesis": "Combine weekly calendar with forecast and priorities",
    },
    "meeting_prep": {
        "patterns": ["prepare for meeting", "meeting with", "before my call", "before my meeting"],
        "tools": ["prepare_for_meeting", "search_emails", "get_todays_events"],
        "synthesis": "Gather relevant emails, context, and related history for the meeting",
    },
    "availability": {
        "patterns": ["am i free", "do i have time", "can i schedule", "what's free"],
        "tools": ["get_todays_events", "get_upcoming_events"],
        "synthesis": "Analyze calendar gaps and commitments",
    },
    "focus_planning": {
        "patterns": ["focus on", "what should i", "priorities", "most important", "should i do"],
        "tools": ["get_priority_items", "get_todays_events", "plan_day"],
        "synthesis": "Combine priorities with calendar to suggest focus areas",
    },
    "inbox_overview": {
        "patterns": ["inbox", "emails", "messages", "what's new"],
        "tools": ["get_email_summary", "get_recent_emails"],
        "synthesis": "Summarize inbox status and highlight important messages",
    },
    "outdoor_planning": {
        "patterns": ["outdoor", "outside", "weather", "walk", "run", "hike"],
        "tools": ["get_current_weather", "get_weather_forecast", "get_todays_events"],
        "synthesis": "Check weather and calendar for outdoor activity planning",
    },
    "person_context": {
        "patterns": ["from ", "involving", "interaction with", "history with", "meeting with", "call with"],
        "tools": ["get_person_context", "search_emails", "get_upcoming_events"],
        "synthesis": "Gather all context about a person including emails and meetings",
    },
    "related_search": {
        "patterns": ["related to", "connected to", "about the project", "regarding"],
        "tools": ["find_related_items", "search_emails", "query_knowledge_base"],
        "synthesis": "Find connections across emails, events, and knowledge base",
    },
}

# Friendlier reasoning strings for pattern matches
PATTERN_REASONING = {
    "day_overview": "I'll combine your schedule, weather, and priorities for a quick overview.",
    "tomorrow_prep": "I'll preview tomorrow's events, weather, and any related emails.",
    "week_overview": "I'll summarize your upcoming week with key events, weather, and priorities.",
    "meeting_prep": "I'll gather emails and calendar context so you're ready for the meeting.",
    "availability": "I'll check your calendar to see when you're free.",
    "focus_planning": "I'll look at priorities and your calendar to suggest what to tackle first.",
    "inbox_overview": "I'll summarize what's in your inbox.",
    "outdoor_planning": "I'll check weather and calendar to help plan outdoor time.",
    "person_context": "You mentioned someone specific, so I'll pull related emails and meetings.",
    "related_search": "I'll look across emails, events, and notes for connected items.",
}


# ============================================================================
# Query Analyzer
# ============================================================================


class QueryAnalyzer:
    """
    Analyzes user queries to determine optimal tool execution strategy.

    This enables:
    - Multi-tool chaining for complex queries
    - Parallel execution of independent tools
    - Intelligent result synthesis
    """

    def __init__(self, use_llm_analysis: bool = True):
        """
        Initialize the query analyzer.

        Args:
            use_llm_analysis: Whether to use LLM for complex query analysis
        """
        self.use_llm_analysis = use_llm_analysis
        self._llm: Optional[LLMClient] = None

    def _get_llm(self) -> LLMClient:
        """Get or create LLM client."""
        if self._llm is None:
            self._llm = LLMClient()
        return self._llm

    def analyze(self, query: str, context: Optional[Dict[str, Any]] = None) -> ToolPlan:
        """
        Analyze a query and create a tool execution plan.

        Args:
            query: The user's query
            context: Additional context (conversation history, user preferences)

        Returns:
            ToolPlan with ordered tools and synthesis strategy
        """
        query_lower = query.lower()

        # Explicitly catch email composition to avoid calendar misfires
        if self._is_email_compose(query_lower):
            return ToolPlan(
                tools=["create_email_draft"],
                parallel_groups=[],
                reasoning="Sounds like you want to send an email. I'll draft it and keep it for your approval.",
                expected_synthesis="Draft the email using the details you provided.",
            )

        # First try pattern matching for known multi-tool queries
        for pattern_name, pattern_config in QUERY_PATTERNS.items():
            if any(p in query_lower for p in pattern_config["patterns"]):
                return ToolPlan(
                    tools=pattern_config["tools"],
                    parallel_groups=self._find_parallel_groups(pattern_config["tools"]),
                    reasoning=self._get_pattern_reasoning(pattern_name, pattern_config),
                    expected_synthesis=pattern_config["synthesis"],
                )

        # Extract entities that might influence tool selection
        entities = self._extract_entities(query)

        # Check for specific tool triggers
        tools_needed = self._identify_tools_from_query(query_lower, entities)

        if len(tools_needed) > 1:
            return ToolPlan(
                tools=self._order_tools(tools_needed),
                parallel_groups=self._find_parallel_groups(tools_needed),
                reasoning=f"Query requires multiple data sources: {', '.join(tools_needed)}",
                expected_synthesis="Combine tool results into a comprehensive answer",
            )
        elif len(tools_needed) == 1:
            return ToolPlan(
                tools=list(tools_needed),
                parallel_groups=[],
                reasoning=f"Single tool query: {list(tools_needed)[0]}",
                expected_synthesis="Present tool result directly",
            )

        # If we can't determine tools, let the LLM decide
        return ToolPlan(
            tools=[],
            parallel_groups=[],
            reasoning="Query doesn't match known patterns - LLM will decide tools dynamically",
            expected_synthesis="Respond based on conversation context",
        )

    def _get_pattern_reasoning(self, pattern_name: str, pattern_config: Dict[str, Any]) -> str:
        """Return a friendly reasoning string for a matched pattern."""
        if pattern_name in PATTERN_REASONING:
            return PATTERN_REASONING[pattern_name]
        return f"I'll combine {', '.join(pattern_config.get('tools', []))} to answer that."

    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """Extract entities from the query."""
        entities = {}
        query_lower = query.lower()

        # Time entities
        time_patterns = {
            "today": "today",
            "tomorrow": "tomorrow",
            "this week": "this_week",
            "next week": "next_week",
            "monday": "monday",
            "tuesday": "tuesday",
            "wednesday": "wednesday",
            "thursday": "thursday",
            "friday": "friday",
        }
        for pattern, value in time_patterns.items():
            if pattern in query_lower:
                entities["time"] = value
                break

        # Person names (basic - could be enhanced with NER)
        if " with " in query_lower:
            after_with = query_lower.split(" with ")[-1].split()[0]
            if after_with and len(after_with) > 2:
                entities["person"] = after_with.title()

        if " from " in query_lower and "email" in query_lower:
            after_from = query_lower.split(" from ")[-1].split()[0]
            if after_from and len(after_from) > 2:
                entities["sender"] = after_from.title()

        return entities

    def _is_email_compose(self, query_lower: str) -> bool:
        """Detect if the user wants to write/send an email."""
        compose_verbs = ["write", "draft", "compose", "send", "shoot", "reach out", "reply", "respond"]
        mentions_email = any(w in query_lower for w in ["email", "mail", "message"])
        has_recipient_hint = "@" in query_lower or " to " in query_lower
        exclusions = ["inbox", "summary", "summarize", "check", "search"]

        if any(ex in query_lower for ex in exclusions):
            return False

        return (mentions_email or has_recipient_hint) and any(v in query_lower for v in compose_verbs)

    def _identify_tools_from_query(self, query_lower: str, entities: Dict[str, Any]) -> Set[str]:
        """Identify which tools are needed based on query content."""
        tools = set()

        # Email composition takes precedence over other calendar heuristics
        if self._is_email_compose(query_lower):
            tools.add("create_email_draft")
            return tools

        # Calendar triggers
        if any(w in query_lower for w in ["calendar", "schedule", "meeting", "event", "busy", "free"]):
            if entities.get("time") == "today":
                tools.add("get_todays_events")
            elif entities.get("time") in ["tomorrow", "this_week", "next_week"]:
                tools.add("get_upcoming_events")
            else:
                tools.add("get_todays_events")

        # Weather triggers
        if any(w in query_lower for w in ["weather", "rain", "sun", "temperature", "cold", "hot", "warm"]):
            if entities.get("time") in ["tomorrow", "this_week", "next_week"]:
                tools.add("get_weather_forecast")
            else:
                tools.add("get_current_weather")

        # Email triggers
        if any(w in query_lower for w in ["email", "inbox", "message", "mail"]):
            if "search" in query_lower or "find" in query_lower or entities.get("sender"):
                tools.add("search_emails")
            elif "summary" in query_lower or "overview" in query_lower:
                tools.add("get_email_summary")
            else:
                tools.add("get_recent_emails")

        # Planning triggers
        if any(w in query_lower for w in ["plan", "priority", "focus", "important", "should"]):
            if "day" in query_lower:
                tools.add("plan_day")
            else:
                tools.add("get_priority_items")

        # Action triggers
        if any(w in query_lower for w in ["pending", "approval", "action", "approve"]):
            tools.add("get_pending_actions")

        # Knowledge triggers
        if any(w in query_lower for w in ["what is", "tell me about", "explain", "how does"]):
            tools.add("query_knowledge_base")

        return tools

    def _order_tools(self, tools: Set[str]) -> List[str]:
        """Order tools based on dependencies and priorities."""
        tool_list = list(tools)

        # Sort by priority (higher first) and dependencies
        def sort_key(tool_name: str) -> Tuple[int, int]:
            dep = TOOL_GRAPH.get(tool_name)
            if dep:
                # Count how many tools in our set depend on this one
                dependents = sum(
                    1
                    for t in tools
                    if t in [d.tool_name for d in TOOL_GRAPH.values() if tool_name in d.required_before]
                )
                return (-dep.priority, -dependents)
            return (0, 0)

        return sorted(tool_list, key=sort_key)

    def _find_parallel_groups(self, tools: List[str]) -> List[List[str]]:
        """Find groups of tools that can run in parallel."""
        if len(tools) <= 1:
            return []

        # Find tools with no dependencies on each other
        parallel_groups = []
        remaining = set(tools)

        while remaining:
            # Find all tools that don't depend on remaining tools
            independent = set()
            for tool in remaining:
                dep = TOOL_GRAPH.get(tool)
                if dep:
                    # Check if any required_before tools are in remaining
                    if not any(r in remaining for r in dep.required_before):
                        independent.add(tool)
                else:
                    independent.add(tool)

            if independent:
                parallel_groups.append(list(independent))
                remaining -= independent
            else:
                # Avoid infinite loop - just add remaining sequentially
                parallel_groups.extend([[t] for t in remaining])
                break

        return parallel_groups

    async def analyze_with_llm(self, query: str, context: Optional[Dict[str, Any]] = None) -> QueryIntent:
        """
        Use LLM for deep query analysis.

        This provides:
        - Intent classification
        - Entity extraction
        - Context understanding
        """
        llm = self._get_llm()

        context_str = ""
        if context and context.get("conversation_history"):
            recent = context["conversation_history"][-3:]
            context_str = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in recent])

        prompt = f"""Analyze this user query for a personal productivity assistant.

Query: "{query}"

{f'Recent conversation context:{chr(10)}{context_str}' if context_str else ''}

Respond with JSON:
{{
    "primary_intent": "main thing the user wants (e.g., 'check calendar', 'plan day', 'find email')",
    "secondary_intents": ["other related intents"],
    "entities": {{
        "people": ["names mentioned"],
        "dates": ["dates/times mentioned"],
        "projects": ["project names"],
        "topics": ["key topics"]
    }},
    "time_context": "today|tomorrow|this_week|specific_date|null",
    "requires_action": true/false
}}"""

        try:
            result = llm.call_json(prompt, temperature=0.1)
            return QueryIntent(
                primary_intent=result.get("primary_intent", "unknown"),
                secondary_intents=result.get("secondary_intents", []),
                entities=result.get("entities", {}),
                time_context=result.get("time_context"),
                requires_action=result.get("requires_action", False),
            )
        except Exception as e:
            logger.error(f"LLM query analysis failed: {e}")
            return QueryIntent(
                primary_intent="unknown",
                secondary_intents=[],
                entities={},
            )


# ============================================================================
# Multi-Tool Executor
# ============================================================================


class MultiToolExecutor:
    """
    Executes multiple tools based on a ToolPlan.

    Features:
    - Parallel execution of independent tools
    - Result aggregation
    - Error handling per tool
    """

    def __init__(self, tool_map: Dict[str, Any]):
        """
        Initialize the executor.

        Args:
            tool_map: Map of tool names to tool instances
        """
        self.tool_map = tool_map

    async def execute(self, plan: ToolPlan, tool_args: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Execute tools according to the plan.

        Args:
            plan: The tool execution plan
            tool_args: Optional arguments for each tool

        Returns:
            Dict mapping tool names to their results
        """
        results = {}
        tool_args = tool_args or {}

        # Execute by parallel groups
        for group in plan.parallel_groups:
            # In a real implementation, we'd use asyncio.gather for parallelism
            for tool_name in group:
                if tool_name in self.tool_map:
                    try:
                        tool = self.tool_map[tool_name]
                        args = tool_args.get(tool_name, {})

                        # Execute tool
                        if hasattr(tool, "ainvoke"):
                            result = await tool.ainvoke(args)
                        elif hasattr(tool, "invoke"):
                            result = tool.invoke(args)
                        elif callable(tool):
                            result = tool(**args)
                            if hasattr(result, "__await__"):
                                result = await result
                        else:
                            result = {"error": f"Unknown tool type: {tool_name}"}

                        results[tool_name] = result

                    except Exception as e:
                        logger.error(f"Tool {tool_name} failed: {e}")
                        results[tool_name] = {"error": str(e)}

        return results

    def synthesize_results(self, results: Dict[str, Any], plan: ToolPlan) -> str:
        """
        Synthesize multiple tool results into a coherent response.

        This is a simple version - the actual synthesis is done by the LLM
        using the tool results as context.
        """
        summaries = []

        for tool_name, result in results.items():
            if isinstance(result, dict) and "error" not in result:
                if hasattr(result, "model_dump"):
                    result = result.model_dump()

                # Extract key information based on tool type
                if tool_name == "get_todays_events":
                    events = result.get("events", [])
                    summaries.append(f"Calendar: {len(events)} events today")
                elif tool_name == "get_current_weather":
                    temp = result.get("temperature", "?")
                    desc = result.get("description", "")
                    summaries.append(f"Weather: {temp}C, {desc}")
                elif tool_name == "get_priority_items":
                    critical = len(result.get("critical", []))
                    high = len(result.get("high", []))
                    summaries.append(f"Priorities: {critical} critical, {high} high")
                elif tool_name == "search_emails":
                    count = result.get("total_found", 0)
                    summaries.append(f"Emails: {count} found")

        return "; ".join(summaries) if summaries else "Data gathered"


# ============================================================================
# Factory Functions
# ============================================================================


def create_query_analyzer() -> QueryAnalyzer:
    """Create a query analyzer instance."""
    return QueryAnalyzer()


def analyze_query(query: str, context: Optional[Dict[str, Any]] = None) -> ToolPlan:
    """Convenience function to analyze a query."""
    analyzer = QueryAnalyzer()
    return analyzer.analyze(query, context)
