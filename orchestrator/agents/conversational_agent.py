"""
Conversational Agent - Main agent for dynamic chat interactions.

This agent uses the ReAct (Reasoning + Acting) pattern to:
1. Understand user intent from natural language
2. Decide which tools to use
3. Execute tools and synthesize responses
4. Maintain conversation context
5. Show visible reasoning to the user

Based on patterns from NVIDIA GenerativeAIExamples.
"""

import json
import logging
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from orchestrator.agents.base import AgentContext, AgentResult, BaseAgent
from orchestrator.agents.query_analyzer import QueryAnalyzer, ToolPlan
from orchestrator.llm_client import LLMClient
from orchestrator.state import OpsAgentState
from orchestrator.tools import ALL_TOOLS
from orchestrator.prompts import build_system_prompt, TOOL_SELECTION_PROMPT

logger = logging.getLogger(__name__)


# ============================================================================
# Tool Descriptions for Visible Reasoning
# ============================================================================

TOOL_DESCRIPTIONS = {
    "plan_day": {
        "thinking": "Let me analyze your inbox and calendar to create a focused plan...",
        "action": "Creating your daily plan",
        "icon": "plan",
    },
    "get_priority_items": {
        "thinking": "Checking your items to find what's most important...",
        "action": "Analyzing priorities",
        "icon": "priority",
    },
    "get_current_weather": {
        "thinking": "Let me check the current weather conditions...",
        "action": "Checking weather",
        "icon": "weather",
    },
    "get_weather_forecast": {
        "thinking": "Looking up the weather forecast...",
        "action": "Getting forecast",
        "icon": "forecast",
    },
    "get_todays_events": {
        "thinking": "Checking your calendar for today...",
        "action": "Reviewing today's events",
        "icon": "calendar",
    },
    "get_upcoming_events": {
        "thinking": "Looking at your upcoming schedule...",
        "action": "Checking upcoming events",
        "icon": "calendar",
    },
    "create_calendar_event": {
        "thinking": "Preparing to add this to your calendar...",
        "action": "Creating calendar event",
        "icon": "add",
    },
    "create_email_draft": {
        "thinking": "Drafting the email details you asked for...",
        "action": "Preparing email draft",
        "icon": "mail",
    },
    "search_emails": {
        "thinking": "Searching through your emails...",
        "action": "Searching inbox",
        "icon": "search",
    },
    "get_recent_emails": {
        "thinking": "Checking your recent messages...",
        "action": "Getting recent emails",
        "icon": "mail",
    },
    "get_email_summary": {
        "thinking": "Analyzing your inbox...",
        "action": "Summarizing inbox",
        "icon": "chart",
    },
    "query_knowledge_base": {
        "thinking": "Searching for relevant information...",
        "action": "Querying knowledge base",
        "icon": "brain",
    },
    "get_pending_actions": {
        "thinking": "Checking for actions that need your attention...",
        "action": "Getting pending actions",
        "icon": "clock",
    },
    "find_related_items": {
        "thinking": "Looking for related information across your data...",
        "action": "Finding connections",
        "icon": "link",
    },
    "get_person_context": {
        "thinking": "Gathering context about this person...",
        "action": "Getting person context",
        "icon": "user",
    },
    "prepare_for_meeting": {
        "thinking": "Preparing comprehensive context for your meeting...",
        "action": "Preparing meeting brief",
        "icon": "note",
    },
}

# Default for unknown tools
DEFAULT_TOOL_DESC = {
    "thinking": "Processing your request...",
    "action": "Executing action",
    "icon": "cog",
}


# ============================================================================
# Suggested Follow-ups
# ============================================================================


class SuggestedAction(BaseModel):
    """A suggested follow-up action."""

    text: str = Field(description="Button text to show user")
    action: str = Field(description="Action type: message, navigate, confirm")
    payload: str = Field(description="Message to send or path to navigate")


FOLLOW_UP_SUGGESTIONS = {
    "plan_day": [
        SuggestedAction(text="Create time blocks", action="message", payload="Create calendar blocks for this plan"),
        SuggestedAction(text="Show my calendar", action="message", payload="What's on my calendar today?"),
    ],
    "get_todays_events": [
        SuggestedAction(
            text="Block focus time", action="message", payload="Block some focus time between my meetings"
        ),
        SuggestedAction(text="Check weather", action="message", payload="What's the weather like today?"),
    ],
    "get_upcoming_events": [
        SuggestedAction(text="Plan this week", action="message", payload="Help me plan this week"),
    ],
    "search_emails": [
        SuggestedAction(text="Show more details", action="message", payload="Tell me more about the first email"),
        SuggestedAction(
            text="Draft a reply", action="message", payload="Help me draft a reply to the most recent one"
        ),
    ],
    "get_current_weather": [
        SuggestedAction(text="Weekly forecast", action="message", payload="What's the forecast for this week?"),
    ],
    "get_weather_forecast": [
        SuggestedAction(
            text="Plan outdoor activity", action="message", payload="When's the best day for outdoor activities?"
        ),
    ],
    "get_pending_actions": [
        SuggestedAction(text="Approve all safe", action="message", payload="Approve all low-risk actions"),
    ],
    "create_calendar_event": [
        SuggestedAction(text="Email the details", action="message", payload="Draft an email to share this event info"),
        SuggestedAction(text="Add a reminder", action="message", payload="Set a 15 minute reminder for that event"),
    ],
    "create_email_draft": [
        SuggestedAction(text="Send it", action="message", payload="Send that email now"),
        SuggestedAction(text="Shorten it", action="message", payload="Rewrite that email to be shorter"),
        SuggestedAction(
            text="Add calendar invite", action="message", payload="Create a calendar invite for this meeting"
        ),
    ],
    "find_related_items": [
        SuggestedAction(text="See more connections", action="message", payload="Show me more related items"),
        SuggestedAction(text="Focus on emails", action="message", payload="Show me just the related emails"),
    ],
    "get_person_context": [
        SuggestedAction(text="Recent emails", action="message", payload="Show me recent emails from this person"),
        SuggestedAction(text="Upcoming meetings", action="message", payload="Do I have any meetings with them?"),
    ],
    "prepare_for_meeting": [
        SuggestedAction(text="Draft talking points", action="message", payload="Help me draft talking points"),
        SuggestedAction(text="Set reminder", action="message", payload="Remind me 10 minutes before"),
    ],
}


# ============================================================================
# ReAct Reasoning Prompt
# ============================================================================

REACT_PROMPT = (
    """Think step by step about what the user needs:

1. What is the user asking for?
2. What information do I need to answer this?
3. Which tool(s) should I use?
4. How should I present the results?

If the question is conversational or doesn't need tools, respond directly.
If tools are needed, call them and synthesize a helpful response from the results.

"""
    + TOOL_SELECTION_PROMPT
)


# ============================================================================
# Agent Output Schemas
# ============================================================================


class ConversationalResponse(BaseModel):
    """Structured response from the conversational agent."""

    content: str = Field(description="The response text to show the user")
    tool_calls_made: List[str] = Field(description="Names of tools that were called", default_factory=list)
    requires_approval: bool = Field(description="Whether any action requires user approval", default=False)
    pending_proposals: List[Dict[str, Any]] = Field(
        description="List of action proposals awaiting approval", default_factory=list
    )
    suggested_actions: List[Dict[str, Any]] = Field(description="Suggested follow-up actions", default_factory=list)
    metadata: Dict[str, Any] = Field(description="Additional metadata about the response", default_factory=dict)


# ============================================================================
# Conversational Agent
# ============================================================================


class ConversationalAgent(BaseAgent):
    """
    Main conversational agent using ReAct pattern with visible reasoning.

    This agent:
    - Understands natural language queries
    - Shows its thinking process to the user
    - Decides which tools to use dynamically
    - Maintains conversation history
    - Offers smart follow-up suggestions
    - Synthesizes helpful responses
    """

    def __init__(
        self,
        name: str = "conversational",
        tools: Optional[List[BaseTool]] = None,
        max_iterations: int = 5,
        use_query_analyzer: bool = True,
        model_provider: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        """
        Initialize the conversational agent.

        Args:
            name: Agent name for identification
            tools: List of tools available to the agent (default: all tools)
            max_iterations: Maximum tool call iterations to prevent infinite loops
            use_query_analyzer: Whether to use QueryAnalyzer for multi-tool planning
            model_provider: Optional provider override ('openai' or 'nvidia')
            model_name: Optional model name override
        """
        super().__init__(name)
        self.tools = tools or ALL_TOOLS
        self.max_iterations = max_iterations
        self.use_query_analyzer = use_query_analyzer
        self.model_provider = model_provider
        self.model_name = model_name
        self._llm: Optional[LLMClient] = None
        self._tool_map: Dict[str, BaseTool] = {}
        self._query_analyzer: Optional[QueryAnalyzer] = None

    def _init_llm(self) -> LLMClient:
        """Initialize and return the LLM client."""
        if self._llm is None:
            self._llm = LLMClient(
                provider=self.model_provider,
                model=self.model_name,
            )
            self._llm.bind_tools(self.tools)
            self._tool_map = {tool.name: tool for tool in self.tools}
        return self._llm

    def _get_query_analyzer(self) -> QueryAnalyzer:
        """Get or create the query analyzer."""
        if self._query_analyzer is None:
            self._query_analyzer = QueryAnalyzer()
        return self._query_analyzer

    def _analyze_query_for_tools(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> ToolPlan:
        """
        Analyze a query to determine which tools to use.

        Returns a ToolPlan with ordered tools and synthesis strategy.
        """
        analyzer = self._get_query_analyzer()
        return analyzer.analyze(user_message, context)

    def _get_tool_description(self, tool_name: str) -> Dict[str, str]:
        """Get human-readable description for a tool."""
        return TOOL_DESCRIPTIONS.get(tool_name, DEFAULT_TOOL_DESC)

    def _get_follow_up_suggestions(self, tools_used: List[str]) -> List[Dict[str, Any]]:
        """Get contextual follow-up suggestions based on tools used."""
        suggestions = []
        seen_texts = set()

        for tool in tools_used:
            if tool in FOLLOW_UP_SUGGESTIONS:
                for suggestion in FOLLOW_UP_SUGGESTIONS[tool]:
                    if suggestion.text not in seen_texts:
                        suggestions.append(suggestion.model_dump())
                        seen_texts.add(suggestion.text)

        # Limit to 3 suggestions
        return suggestions[:3]

    def _build_system_prompt(self, context: AgentContext) -> str:
        """Build the system prompt with context."""
        now = datetime.now()

        # Get user context
        user_context = context.metadata.get("user_context", {})

        return build_system_prompt(
            current_time=now,
            timezone=user_context.get("timezone", "UTC"),
            location=user_context.get("location"),
        )

    def _build_messages(
        self,
        user_message: str,
        context: AgentContext,
        system_prompt: str,
    ) -> List[BaseMessage]:
        """Build the message list for the LLM."""
        messages = [SystemMessage(content=system_prompt)]

        # Add conversation history
        conversation_history = context.metadata.get("conversation_history", [])
        for msg in conversation_history[-10:]:  # Last 10 messages for context
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        # Add current message with reasoning prompt
        messages.append(HumanMessage(content=f"{user_message}\n\n{REACT_PROMPT}"))

        return messages

    def _analyze_query_complexity(self, user_message: str) -> Dict[str, Any]:
        """Analyze the query to provide better reasoning messages."""
        message_lower = user_message.lower()

        analysis = {
            "needs_calendar": any(
                w in message_lower for w in ["calendar", "schedule", "meeting", "event", "today", "tomorrow", "week"]
            ),
            "needs_email": any(w in message_lower for w in ["email", "inbox", "message", "from", "mail"]),
            "needs_weather": any(w in message_lower for w in ["weather", "rain", "sun", "temperature", "forecast"]),
            "needs_planning": any(w in message_lower for w in ["plan", "focus", "priority", "important", "should i"]),
            "is_greeting": any(w in message_lower for w in ["hello", "hi", "hey", "good morning", "good afternoon"]),
            "is_question": "?" in user_message
            or any(w in message_lower for w in ["what", "when", "where", "how", "why", "who"]),
        }

        return analysis

    def _generate_initial_reasoning(self, user_message: str, analysis: Dict[str, Any]) -> str:
        """Generate an initial reasoning message based on query analysis."""
        if analysis["is_greeting"]:
            return "Hello! Let me see how I can help you today..."

        parts = []
        if analysis["needs_calendar"]:
            parts.append("checking your calendar")
        if analysis["needs_email"]:
            parts.append("looking at your emails")
        if analysis["needs_weather"]:
            parts.append("checking the weather")
        if analysis["needs_planning"]:
            parts.append("analyzing your priorities")

        if parts:
            return f"Let me help with that. I'll be {', '.join(parts)}..."
        elif analysis["is_question"]:
            return "Let me think about that..."
        else:
            return "Processing your request..."

    async def run(self, context: Union[AgentContext, OpsAgentState]) -> AgentResult:
        """
        Execute the conversational agent.

        Args:
            context: Agent context with user message and conversation history

        Returns:
            AgentResult with the response
        """
        start_time = datetime.now()
        ctx = self._get_context(context)

        try:
            llm = self._init_llm()

            # Get user message from context
            user_message = ctx.metadata.get("message", "")
            if not user_message:
                # Check items for a message
                for item in ctx.items:
                    if item.get("type") == "message":
                        user_message = item.get("content", "")
                        break

            if not user_message:
                return self._create_result(
                    status="error",
                    error_message="No user message provided",
                    duration_ms=self._elapsed_ms(start_time),
                )

            # Build prompts and messages
            system_prompt = self._build_system_prompt(ctx)
            messages = self._build_messages(user_message, ctx, system_prompt)

            # Run the ReAct loop
            response = await self._react_loop(llm, messages, ctx)

            return self._create_result(
                status="success",
                output_summary={
                    "response": response.content,
                    "tools_used": response.tool_calls_made,
                    "requires_approval": response.requires_approval,
                    "suggested_actions": response.suggested_actions,
                },
                action_proposals=response.pending_proposals,
                duration_ms=self._elapsed_ms(start_time),
            )

        except Exception as e:
            logger.error(f"Conversational agent error: {e}", exc_info=True)
            return self._create_result(
                status="error",
                error_message=str(e),
                duration_ms=self._elapsed_ms(start_time),
            )

    async def _react_loop(
        self,
        llm: LLMClient,
        messages: List[BaseMessage],
        context: AgentContext,
    ) -> ConversationalResponse:
        """
        Execute the ReAct reasoning loop.

        Calls the LLM, checks for tool calls, executes tools,
        and continues until a final response is ready.
        """
        tools_called = []
        pending_proposals = []
        iterations = 0

        while iterations < self.max_iterations:
            iterations += 1

            # Call LLM
            response = await llm.ainvoke_messages(messages)

            # Check for tool calls
            tool_calls = getattr(response, "tool_calls", [])

            if not tool_calls:
                # No more tool calls - we have the final response
                content = response.content if hasattr(response, "content") else str(response)

                # Get follow-up suggestions
                suggested_actions = self._get_follow_up_suggestions(tools_called)

                return ConversationalResponse(
                    content=content,
                    tool_calls_made=tools_called,
                    requires_approval=len(pending_proposals) > 0,
                    pending_proposals=pending_proposals,
                    suggested_actions=suggested_actions,
                    metadata={"iterations": iterations},
                )

            # Execute tool calls
            messages.append(response)  # Add AI message with tool calls

            for tool_call in tool_calls:
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("args", {})
                tool_id = tool_call.get("id", f"call_{len(tools_called)}")

                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                tools_called.append(tool_name)

                # Get and execute the tool
                tool = self._tool_map.get(tool_name)
                if tool:
                    try:
                        result = await self._execute_tool(tool, tool_args)

                        # Check if result requires approval
                        if hasattr(result, "requires_approval") and result.requires_approval:
                            if hasattr(result, "proposal_id") and result.proposal_id:
                                # Fetch full proposal from database
                                full_proposal = self._fetch_proposal_from_db(result.proposal_id)
                                if full_proposal:
                                    pending_proposals.append(full_proposal)

                        # Convert result to string for message
                        if hasattr(result, "model_dump"):
                            result_str = json.dumps(result.model_dump(), default=str)
                        else:
                            result_str = str(result)

                        messages.append(
                            ToolMessage(
                                content=result_str,
                                tool_call_id=tool_id,
                            )
                        )

                    except Exception as e:
                        logger.error(f"Tool {tool_name} failed: {e}")
                        messages.append(
                            ToolMessage(
                                content=f"Error executing {tool_name}: {str(e)}",
                                tool_call_id=tool_id,
                            )
                        )
                else:
                    messages.append(
                        ToolMessage(
                            content=f"Unknown tool: {tool_name}",
                            tool_call_id=tool_id,
                        )
                    )

        # Max iterations reached - return what we have
        logger.warning(f"Max iterations ({self.max_iterations}) reached")
        suggested_actions = self._get_follow_up_suggestions(tools_called)

        return ConversationalResponse(
            content="I'm still processing your request. Please try asking in a different way.",
            tool_calls_made=tools_called,
            requires_approval=len(pending_proposals) > 0,
            pending_proposals=pending_proposals,
            suggested_actions=suggested_actions,
            metadata={"iterations": iterations, "max_reached": True},
        )

    async def _execute_tool(self, tool: BaseTool, args: Dict[str, Any]) -> Any:
        """Execute a tool with the given arguments."""
        # Tools can be sync or async
        if hasattr(tool, "ainvoke"):
            return await tool.ainvoke(args)
        elif hasattr(tool, "invoke"):
            return tool.invoke(args)
        elif callable(tool):
            result = tool(**args)
            # If result is a coroutine, await it
            if hasattr(result, "__await__"):
                return await result
            return result
        else:
            raise ValueError(f"Don't know how to execute tool: {tool}")

    def _elapsed_ms(self, start_time: datetime) -> int:
        """Calculate elapsed milliseconds."""
        return int((datetime.now() - start_time).total_seconds() * 1000)

    def _fetch_proposal_from_db(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch full proposal details from database.

        Args:
            proposal_id: The UUID of the proposal

        Returns:
            Dictionary with full proposal data for frontend, or None if not found
        """
        try:
            from backend.api.models import ActionProposal
            from orchestrator.tools.calendar import _get_db_session
            import uuid

            db = _get_db_session()
            try:
                proposal = db.query(ActionProposal).filter(ActionProposal.id == uuid.UUID(proposal_id)).first()

                if proposal:
                    return {
                        "id": str(proposal.id),
                        "agent_name": proposal.agent_name,
                        "action_type": proposal.action_type,
                        "payload": proposal.payload,
                        "status": proposal.status,
                        "risk_level": proposal.risk_level,
                        "explanation": proposal.explanation,
                    }
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to fetch proposal {proposal_id}: {e}")

        return None

    # ========================================================================
    # Streaming Interface with Visible Reasoning
    # ========================================================================

    async def stream(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream the agent response with visible reasoning.

        Yields events that show the agent's thinking process:
        - reasoning: What the agent is thinking
        - tool_start: Starting to use a tool
        - tool_progress: Tool execution status
        - tool_result: Tool returned data
        - insight: Key insights from data
        - response: Final response
        - suggestions: Follow-up suggestions

        Args:
            user_message: The user's message
            conversation_history: Previous messages in the conversation
            user_context: User context (location, timezone, etc.)

        Yields:
            Events with type and content
        """
        # Initialize LLM with model from context
        model_provider = (user_context or {}).get("model_provider") or (user_context or {}).get("modelProvider")
        model_name = (user_context or {}).get("model_name") or (user_context or {}).get("modelName")

        # Update instance variables if provided in context
        if model_provider and not self.model_provider:
            self.model_provider = model_provider
        if model_name and not self.model_name:
            self.model_name = model_name

        llm = self._init_llm()

        # Analyze the query
        query_analysis = self._analyze_query_complexity(user_message)

        # Get multi-tool plan if enabled
        tool_plan: Optional[ToolPlan] = None
        if self.use_query_analyzer:
            tool_plan = self._analyze_query_for_tools(
                user_message, {"conversation_history": conversation_history or []}
            )

        # Build context
        ctx = AgentContext(
            user_id="default",
            intent="conversation",
            items=[],
            metadata={
                "message": user_message,
                "conversation_history": conversation_history or [],
                "user_context": user_context or {},
                "tool_plan": tool_plan.model_dump() if tool_plan else None,
            },
        )

        system_prompt = self._build_system_prompt(ctx)
        messages = self._build_messages(user_message, ctx, system_prompt)

        tools_called = []
        pending_proposals = []
        iterations = 0

        # Initial reasoning - enhanced with tool plan
        if tool_plan and tool_plan.tools:
            initial_reasoning = f"I'll help with that. {tool_plan.reasoning}"
            yield {
                "type": "reasoning",
                "content": initial_reasoning,
                "step": "planning",
                "planned_tools": tool_plan.tools,
            }
        else:
            initial_reasoning = self._generate_initial_reasoning(user_message, query_analysis)
            yield {
                "type": "reasoning",
                "content": initial_reasoning,
                "step": "understanding",
            }

        while iterations < self.max_iterations:
            iterations += 1

            # Show thinking state
            if iterations > 1:
                yield {
                    "type": "reasoning",
                    "content": "Analyzing the results and thinking about what else might help...",
                    "step": "analyzing",
                }

            # Call LLM with timeout protection
            try:
                import asyncio

                response = await asyncio.wait_for(
                    llm.ainvoke_messages(messages), timeout=120.0  # 2 minute timeout per LLM call
                )
            except asyncio.TimeoutError:
                logger.error("LLM call timed out after 120 seconds")
                yield {
                    "type": "error",
                    "error": "The request took too long. Please try again with a simpler query.",
                }
                return
            except Exception as e:
                logger.error(f"LLM call failed: {e}", exc_info=True)
                yield {
                    "type": "error",
                    "error": f"Failed to process request: {str(e)}",
                }
                return

            # Check for tool calls
            tool_calls = getattr(response, "tool_calls", [])

            if not tool_calls:
                # Final response
                content = response.content if hasattr(response, "content") else str(response)

                # Get follow-up suggestions
                suggested_actions = self._get_follow_up_suggestions(tools_called)

                # Yield final response
                yield {
                    "type": "response",
                    "content": content,
                    "tools_used": tools_called,
                    "requires_approval": len(pending_proposals) > 0,
                    "proposals": pending_proposals,
                }

                # Yield suggestions if any
                if suggested_actions:
                    yield {
                        "type": "suggestions",
                        "actions": suggested_actions,
                    }

                return

            # Execute tool calls with visible reasoning
            messages.append(response)

            for tool_call in tool_calls:
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("args", {})
                tool_id = tool_call.get("id", f"call_{len(tools_called)}")

                # Get tool description for visible reasoning
                tool_desc = self._get_tool_description(tool_name)

                # Yield thinking event
                yield {
                    "type": "reasoning",
                    "content": tool_desc["thinking"],
                    "step": "tool_decision",
                    "tool": tool_name,
                }

                # Yield tool start event
                yield {
                    "type": "tool_start",
                    "tool": tool_name,
                    "action": tool_desc["action"],
                    "icon": tool_desc["icon"],
                    "args": tool_args,
                }

                tools_called.append(tool_name)
                tool = self._tool_map.get(tool_name)

                if tool:
                    try:
                        result = await self._execute_tool(tool, tool_args)

                        # Check for approval requirements
                        if hasattr(result, "requires_approval") and result.requires_approval:
                            if hasattr(result, "proposal_id") and result.proposal_id:
                                # Fetch full proposal from database
                                full_proposal = self._fetch_proposal_from_db(result.proposal_id)
                                if full_proposal:
                                    pending_proposals.append(full_proposal)

                        # Convert result
                        if hasattr(result, "model_dump"):
                            result_dict = result.model_dump()
                            result_str = json.dumps(result_dict, default=str)
                        else:
                            result_dict = {"result": str(result)}
                            result_str = str(result)

                        # Extract key insight from result
                        insight = self._extract_insight(tool_name, result_dict)

                        # Yield tool result
                        yield {
                            "type": "tool_result",
                            "tool": tool_name,
                            "icon": tool_desc["icon"],
                            "result": result_dict,
                            "success": True,
                        }

                        # Yield insight if we have one
                        if insight:
                            yield {
                                "type": "insight",
                                "content": insight,
                                "source": tool_name,
                            }

                        messages.append(
                            ToolMessage(
                                content=result_str,
                                tool_call_id=tool_id,
                            )
                        )

                    except Exception as e:
                        yield {
                            "type": "tool_error",
                            "tool": tool_name,
                            "error": str(e),
                        }

                        yield {
                            "type": "reasoning",
                            "content": "Hmm, I had trouble with that. Let me try a different approach...",
                            "step": "error_recovery",
                        }

                        messages.append(
                            ToolMessage(
                                content=f"Error: {str(e)}",
                                tool_call_id=tool_id,
                            )
                        )
                else:
                    yield {
                        "type": "tool_error",
                        "tool": tool_name,
                        "error": f"Unknown tool: {tool_name}",
                    }
                    messages.append(
                        ToolMessage(
                            content=f"Unknown tool: {tool_name}",
                            tool_call_id=tool_id,
                        )
                    )

        # Max iterations
        yield {
            "type": "reasoning",
            "content": "I've gathered a lot of information. Let me put it together...",
            "step": "synthesizing",
        }

        suggested_actions = self._get_follow_up_suggestions(tools_called)

        yield {
            "type": "response",
            "content": (
                "I've analyzed several aspects of your request. Could you help me focus "
                "on what's most important to you?"
            ),
            "tools_used": tools_called,
            "requires_approval": len(pending_proposals) > 0,
            "proposals": pending_proposals,
            "max_iterations_reached": True,
        }

        if suggested_actions:
            yield {
                "type": "suggestions",
                "actions": suggested_actions,
            }

    def _extract_insight(self, tool_name: str, result: Dict[str, Any]) -> Optional[str]:
        """Extract a key insight from tool results to show the user."""
        try:
            if tool_name == "get_todays_events":
                events = result.get("events", [])
                if not events:
                    return "Your calendar is clear today!"
                elif len(events) == 1:
                    return "You have 1 event today"
                else:
                    return f"Found {len(events)} events on your calendar today"

            elif tool_name == "get_upcoming_events":
                events = result.get("events", [])
                summary = result.get("summary", "")
                if summary:
                    return summary
                return f"Found {len(events)} upcoming events"

            elif tool_name == "search_emails":
                emails = result.get("emails", [])
                total = result.get("total_found", len(emails))
                if total == 0:
                    return "No matching emails found"
                return f"Found {total} matching emails"

            elif tool_name == "get_current_weather":
                temp = result.get("temperature", "")
                desc = result.get("description", "")
                if temp and desc:
                    return f"Currently {temp}C and {desc.lower()}"

            elif tool_name == "get_weather_forecast":
                summary = result.get("summary", "")
                if summary:
                    return summary

            elif tool_name == "plan_day":
                must_do = result.get("must_do_today", [])
                if must_do:
                    return f"Identified {len(must_do)} key priorities for today"

            elif tool_name == "get_priority_items":
                critical = len(result.get("critical", []))
                high = len(result.get("high", []))
                if critical > 0:
                    return f"Found {critical} critical items needing attention"
                elif high > 0:
                    return f"Found {high} high priority items"

            elif tool_name == "get_pending_actions":
                actions = result.get("actions", [])
                if not actions:
                    return "No pending actions - you're all caught up!"
                return f"Found {len(actions)} actions awaiting your approval"

            elif tool_name == "query_knowledge_base":
                has_context = result.get("has_context", False)
                confidence = result.get("confidence", "low")
                if has_context and confidence in ["high", "medium"]:
                    return "Found relevant information"

        except Exception as e:
            logger.debug(f"Error extracting insight: {e}")

        return None


# ============================================================================
# Factory Functions
# ============================================================================


def create_conversational_agent(
    tools: Optional[List[BaseTool]] = None,
) -> ConversationalAgent:
    """Create a conversational agent with optional custom tools."""
    return ConversationalAgent(tools=tools)


def get_default_agent() -> ConversationalAgent:
    """Get the default conversational agent with all tools."""
    return ConversationalAgent()
