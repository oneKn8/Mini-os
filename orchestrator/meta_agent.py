"""
MetaAgent: Intelligent agent controller that dynamically creates specialized agents.

Replaces hardcoded agent types with AI-driven agent creation based on task analysis.
"""

import logging
from typing import List, Optional, Union
from pydantic import BaseModel

from orchestrator.agents.base import BaseAgent, AgentContext
from orchestrator.llm_client import LLMClient
from orchestrator.state import OpsAgentState

logger = logging.getLogger(__name__)


class TaskAnalysis(BaseModel):
    """Analysis of a task to determine execution strategy."""

    task_type: str
    complexity: str
    required_capabilities: List[str]
    suggested_tools: List[str]
    reasoning: str
    orchestration_strategy: str


class MetaAgent:
    """
    Meta-agent that dynamically creates specialized agents based on task analysis.

    This replaces the hardcoded approach of having 8 specific agent types
    with an intelligent system that:
    1. Analyzes the task using LLM reasoning
    2. Determines what capabilities and tools are needed
    3. Creates a DynamicAgent with the appropriate tools
    4. Orchestrates execution
    5. Synthesizes results
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize MetaAgent.

        Args:
            llm_client: Optional LLM client for task analysis
        """
        self.llm_client = llm_client or LLMClient()
        self.tool_registry = None

    def set_tool_registry(self, tool_registry):
        """Set the tool registry for dynamic tool discovery."""
        self.tool_registry = tool_registry

    async def analyze_task(self, user_message: str, context: Union[AgentContext, OpsAgentState]) -> TaskAnalysis:
        """
        Analyze a task to determine execution strategy.

        Args:
            user_message: The user's request
            context: Execution context

        Returns:
            TaskAnalysis with recommendations
        """
        agent_ctx = self._get_context(context)

        analysis_prompt = f"""Analyze this user request and determine the best execution strategy.

User Request: {user_message}

User Context:
- User ID: {agent_ctx.user_id}
- Intent: {agent_ctx.intent}
- Available items: {len(agent_ctx.items)} items
- User preferences: {list(agent_ctx.user_preferences.keys())}

Please analyze:
1. Task Type (e.g., email_management, calendar_management, planning, query, multi_domain)
2. Complexity (simple, moderate, complex)
3. Required Capabilities (e.g., email, calendar, weather, planning, knowledge)
4. Suggested Tools (specific tools needed)
5. Orchestration Strategy (single_shot, sequential, parallel, iterative)

Respond with a JSON object:
{{
  "task_type": "...",
  "complexity": "...",
  "required_capabilities": ["...", "..."],
  "suggested_tools": ["...", "..."],
  "reasoning": "Brief explanation of your analysis",
  "orchestration_strategy": "..."
}}
"""

        try:
            structured_llm = self.llm_client.with_structured_output(TaskAnalysis)
            response = await structured_llm.ainvoke([{"role": "user", "content": analysis_prompt}])

            if isinstance(response, TaskAnalysis):
                logger.info(f"Task analysis complete: {response.task_type} ({response.complexity})")
                return response
            else:
                logger.warning("Task analysis did not return TaskAnalysis, creating default")
                return self._create_default_analysis(user_message)

        except Exception as e:
            logger.error(f"Task analysis failed: {e}, using defaults")
            return self._create_default_analysis(user_message)

    def _create_default_analysis(self, user_message: str) -> TaskAnalysis:
        """Create a default task analysis when LLM analysis fails."""
        message_lower = user_message.lower()

        task_type = "query"
        capabilities = []
        tools = []

        if any(word in message_lower for word in ["email", "inbox", "mail", "message"]):
            task_type = "email_management"
            capabilities = ["email"]
            tools = ["search_emails", "get_recent_emails", "create_email_draft"]
        elif any(word in message_lower for word in ["calendar", "event", "meeting", "schedule"]):
            task_type = "calendar_management"
            capabilities = ["calendar"]
            tools = ["get_todays_events", "get_upcoming_events", "create_calendar_event"]
        elif any(word in message_lower for word in ["weather", "forecast", "temperature"]):
            task_type = "weather_query"
            capabilities = ["weather"]
            tools = ["get_current_weather", "get_weather_forecast"]
        elif any(word in message_lower for word in ["plan", "organize", "prioritize"]):
            task_type = "planning"
            capabilities = ["planning", "calendar"]
            tools = ["plan_day", "get_priority_items", "get_upcoming_events"]

        return TaskAnalysis(
            task_type=task_type,
            complexity="moderate",
            required_capabilities=capabilities or ["query"],
            suggested_tools=tools or ["query_knowledge_base"],
            reasoning="Default analysis based on keyword matching",
            orchestration_strategy="sequential",
        )

    async def create_agent(self, task_analysis: TaskAnalysis) -> BaseAgent:
        """
        Create a specialized agent based on task analysis.

        Args:
            task_analysis: Analysis of the task

        Returns:
            Configured DynamicAgent or ConversationalAgent
        """
        from orchestrator.agents.dynamic_agent import DynamicAgent
        from orchestrator.agents.conversational_agent import ConversationalAgent

        if not self.tool_registry:
            logger.warning("No tool registry set, falling back to ConversationalAgent")
            return ConversationalAgent(llm_client=self.llm_client)

        selected_tools = self.tool_registry.find_tools_for_capabilities(
            task_analysis.required_capabilities, task_analysis.suggested_tools
        )

        if not selected_tools:
            logger.warning("No tools found, falling back to ConversationalAgent")
            return ConversationalAgent(llm_client=self.llm_client)

        logger.info(f"Creating DynamicAgent with {len(selected_tools)} tools for {task_analysis.task_type}")

        return DynamicAgent(
            capabilities=task_analysis.required_capabilities,
            tools=selected_tools,
            reasoning_mode="react",
            llm_client=self.llm_client,
        )

    async def execute(
        self,
        user_message: str,
        context: Union[AgentContext, OpsAgentState],
        stream: bool = False,
    ):
        """
        Execute a task end-to-end with dynamic agent creation.

        Args:
            user_message: The user's request
            context: Execution context
            stream: Whether to stream results

        Returns:
            AgentResult or async generator if streaming
        """
        task_analysis = await self.analyze_task(user_message, context)

        agent = await self.create_agent(task_analysis)

        if stream:
            return self._execute_streaming(agent, user_message, context, task_analysis)
        else:
            result = await agent.run(context)
            result.metadata_updates.append(
                {
                    "meta_analysis": {
                        "task_type": task_analysis.task_type,
                        "complexity": task_analysis.complexity,
                        "tools_used": task_analysis.suggested_tools,
                    }
                }
            )
            return result

    async def _execute_streaming(self, agent, user_message, context, task_analysis):
        """Execute agent with streaming support."""
        if hasattr(agent, "stream"):
            async for event in agent.stream(user_message, context):
                if event.get("type") == "reasoning" and event.get("step") == "understanding":
                    event["meta_analysis"] = {
                        "task_type": task_analysis.task_type,
                        "complexity": task_analysis.complexity,
                        "strategy": task_analysis.orchestration_strategy,
                    }
                yield event
        else:
            result = await agent.run(context)
            yield {
                "type": "message",
                "content": result.output_summary.get("response", "Task completed."),
            }

    def _get_context(self, input_data: Union[AgentContext, OpsAgentState]) -> AgentContext:
        """Convert input to AgentContext for compatibility."""
        if isinstance(input_data, OpsAgentState):
            return AgentContext.from_state(input_data)
        return input_data
