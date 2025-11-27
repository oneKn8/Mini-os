"""
DynamicAgent: A single adaptable agent that handles any task based on capabilities.

Replaces specialized agent classes with one intelligent agent that adapts to
any combination of tools and capabilities.
"""

import logging
import time
from typing import AsyncIterator, Dict, List, Optional, Union

from langchain_core.tools import BaseTool

from orchestrator.agents.base import AgentContext, AgentResult, BaseAgent
from orchestrator.agents.conversational_agent import ConversationalAgent
from orchestrator.llm_client import LLMClient
from orchestrator.state import OpsAgentState

logger = logging.getLogger(__name__)


class DynamicAgent(BaseAgent):
    """
    A single adaptable agent that can handle any task.

    Instead of having EmailAgent, CalendarAgent, etc., we have one intelligent
    agent that adapts based on:
    - Capabilities provided (email, calendar, planning, etc.)
    - Tools available
    - Reasoning mode (react, plan_execute, tree_of_thought)
    """

    def __init__(
        self,
        capabilities: List[str],
        tools: List[BaseTool],
        reasoning_mode: str = "react",
        llm_client: Optional[LLMClient] = None,
        name: Optional[str] = None,
    ):
        """
        Initialize DynamicAgent.

        Args:
            capabilities: List of capabilities (e.g., ["email", "calendar"])
            tools: Tools available to the agent
            reasoning_mode: Reasoning approach ("react", "plan_execute", "tree_of_thought")
            llm_client: Optional LLM client
            name: Optional agent name
        """
        agent_name = name or f"DynamicAgent[{','.join(capabilities[:2])}]"
        super().__init__(agent_name)

        self.capabilities = capabilities
        self.tools = tools
        self.reasoning_mode = reasoning_mode
        self.llm_client = llm_client or LLMClient()

        self._conversational_agent = ConversationalAgent(
            llm_client=self.llm_client,
            tools=self.tools,
        )

        logger.info(f"Initialized {self.name} with {len(tools)} tools and mode={reasoning_mode}")

    async def run(self, context: Union[AgentContext, OpsAgentState]) -> AgentResult:
        """
        Execute the agent.

        Args:
            context: Execution context

        Returns:
            AgentResult with outputs
        """
        start_time = time.time()

        try:
            agent_ctx = self._get_context(context)

            system_prompt = self._build_system_prompt(agent_ctx)

            user_message = agent_ctx.metadata.get("user_message", "")
            if not user_message:
                user_message = f"Help me with {agent_ctx.intent}"

            self._conversational_agent.set_system_prompt(system_prompt)

            result = await self._conversational_agent.run(context)

            duration_ms = int((time.time() - start_time) * 1000)

            return AgentResult(
                agent_name=self.name,
                status=result.status,
                output_summary={
                    "response": result.output_summary.get("response", ""),
                    "capabilities_used": self.capabilities,
                    "tools_available": [t.name for t in self.tools],
                },
                action_proposals=result.action_proposals,
                metadata_updates=result.metadata_updates,
                error_message=result.error_message,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"{self.name} execution failed: {e}")
            return self._create_result(
                status="error",
                error_message=str(e),
                duration_ms=duration_ms,
            )

    async def stream(self, user_message: str, context: Union[AgentContext, OpsAgentState]) -> AsyncIterator[Dict]:
        """
        Stream agent execution with real-time events.

        Args:
            user_message: User's message
            context: Execution context

        Yields:
            Event dictionaries
        """
        try:
            agent_ctx = self._get_context(context)

            system_prompt = self._build_system_prompt(agent_ctx)

            self._conversational_agent.set_system_prompt(system_prompt)

            yield {
                "type": "agent_status",
                "agent": self.name,
                "status": "initialized",
                "capabilities": self.capabilities,
                "tools": [t.name for t in self.tools],
            }

            async for event in self._conversational_agent.stream(user_message, context):
                if "agent" not in event:
                    event["agent"] = self.name
                if "capabilities" not in event:
                    event["capabilities"] = self.capabilities
                yield event

        except Exception as e:
            logger.error(f"{self.name} streaming failed: {e}")
            yield {"type": "error", "agent": self.name, "error": str(e)}

    def _build_system_prompt(self, context: AgentContext) -> str:
        """Build system prompt based on capabilities."""
        capabilities_str = ", ".join(self.capabilities)
        base_prompt = (
            "You are a helpful AI assistant with the following capabilities: "
            f"{capabilities_str}.\n\n"
            "Your goal is to help the user accomplish their task using the available tools effectively."
        )

        if "email" in self.capabilities:
            base_prompt += """

Email Management:
- Search and retrieve emails
- Analyze email content and extract key information
- Draft professional email responses
- Suggest actions based on email content"""

        if "calendar" in self.capabilities:
            base_prompt += """

Calendar Management:
- View upcoming events and schedule
- Create and update calendar events
- Find optimal meeting times
- Suggest time-based actions"""

        if "planning" in self.capabilities:
            base_prompt += """

Planning & Organization:
- Analyze priorities and deadlines
- Create daily/weekly plans
- Organize tasks efficiently
- Suggest time management improvements"""

        if "weather" in self.capabilities:
            base_prompt += """

Weather Information:
- Provide current weather conditions
- Give weather forecasts
- Suggest weather-appropriate activities"""

        if "knowledge" in self.capabilities:
            base_prompt += """

Knowledge & Information:
- Answer questions using available knowledge
- Retrieve relevant information
- Provide context and explanations"""

        user_context = []
        if context.user_preferences:
            user_context.append(f"User preferences: {context.user_preferences}")
        if context.weather_context:
            user_context.append(f"Weather: {context.weather_context}")

        if user_context:
            base_prompt += "\n\nContext:\n" + "\n".join(user_context)

        tool_names = ", ".join(t.name for t in self.tools)
        base_prompt += f"\n\nAvailable tools: {tool_names}"
        base_prompt += (
            "\n\nUse tools when needed to accomplish the task. Think step-by-step and explain your reasoning."
        )

        return base_prompt

    def get_capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return self.capabilities.copy()

    def get_tools(self) -> List[BaseTool]:
        """Get agent tools."""
        return self.tools.copy()

    def set_system_prompt(self, prompt: str):
        """Set custom system prompt."""
        self._conversational_agent.set_system_prompt(prompt)

    def __repr__(self) -> str:
        return f"DynamicAgent(capabilities={self.capabilities}, tools={len(self.tools)}, mode={self.reasoning_mode})"
