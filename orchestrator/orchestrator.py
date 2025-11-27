"""
Dynamic Multi-Agent Orchestrator using MetaAgent.

Replaces hardcoded agent workflow with intelligent, dynamic agent creation.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy.orm import Session

from backend.executor.action_executor import ActionExecutor
from backend.api.models import ActionProposal
from orchestrator.agents.base import AgentContext, AgentResult
from orchestrator.agents.conversational_agent import ConversationalAgent
from orchestrator.meta_agent import MetaAgent
from orchestrator.tool_registry import ToolRegistry
from orchestrator.registry import AgentRegistry
from orchestrator.state import OpsAgentState
from orchestrator.tools import ALL_TOOLS

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationResult:
    """Result from orchestrating agents."""

    status: str
    results: Dict[str, AgentResult]
    execution_time_ms: int
    error: str = None


class Orchestrator:
    """
    Dynamic orchestrator using MetaAgent for intelligent task routing.

    This replaces the previous rigid workflow with 8 hardcoded agents
    with an intelligent system that analyzes tasks and creates
    specialized agents dynamically.
    """

    def __init__(self):
        self.registry = AgentRegistry()
        self.tool_registry = ToolRegistry()
        self.meta_agent = None

        self._initialize_tool_registry()
        self._initialize_meta_agent()
        self._register_fallback_agent()

        self.checkpointer = MemorySaver()
        self.workflow = self._build_workflow()

    def _initialize_tool_registry(self):
        """Initialize tool registry with all available tools."""
        self.tool_registry.register_tools_from_list(ALL_TOOLS)
        logger.info(f"Initialized tool registry with {len(self.tool_registry)} tools")
        logger.info(f"Available capabilities: {self.tool_registry.list_capabilities()}")

    def _initialize_meta_agent(self):
        """Initialize MetaAgent with tool registry."""
        self.meta_agent = MetaAgent()
        self.meta_agent.set_tool_registry(self.tool_registry)
        logger.info("Initialized MetaAgent")

    def _register_fallback_agent(self):
        """Register ConversationalAgent as fallback."""
        fallback_agent = ConversationalAgent(tools=ALL_TOOLS)
        self.registry.register("conversational", fallback_agent)
        logger.info("Registered fallback ConversationalAgent")

    def _build_workflow(self) -> StateGraph:
        """
        Build simplified workflow with MetaAgent.

        The workflow now has just two nodes:
        1. MetaAgent - Analyzes task and executes with dynamic agents
        2. ActionExecutor - Handles action approvals
        """
        workflow = StateGraph(OpsAgentState)

        workflow.add_node("meta_agent", self._meta_agent_node)
        workflow.add_node("action_executor", self._action_executor_node)

        workflow.set_entry_point("meta_agent")

        workflow.add_conditional_edges(
            "meta_agent",
            self._route_to_executor,
            {"action_executor": "action_executor", "end": END},
        )

        workflow.add_edge("action_executor", END)

        return workflow.compile(checkpointer=self.checkpointer, interrupt_before=["action_executor"])

    def _route_to_executor(self, state) -> str:
        """Route to action executor if there are pending actions."""
        proposals = state.get("action_proposals", []) if isinstance(state, dict) else state.action_proposals
        if any(p.get("status") == "pending" for p in proposals):
            return "action_executor"
        return "end"

    def build_context(self, intent: str, items: List[Dict], user_id: str, user_message: str = "") -> AgentContext:
        """Build initial context for orchestration."""
        return AgentContext(
            user_id=user_id,
            intent=intent,
            items=items,
            user_preferences={},
            weather_context={},
            metadata={"user_message": user_message},
            action_proposals=[],
        )

    def _ensure_state(self, state) -> OpsAgentState:
        """Convert dict state to OpsAgentState if needed."""
        if isinstance(state, dict):
            return OpsAgentState(**state)
        return state

    def _state_to_dict(self, state: OpsAgentState) -> dict:
        """Convert OpsAgentState to dict for LangGraph."""
        return state.model_dump()

    async def _meta_agent_node(self, state) -> dict:
        """
        MetaAgent node - intelligently handles all tasks.

        This replaces the previous triage/safety/email/event/planner/preference/rag nodes
        with a single intelligent node that:
        1. Analyzes the task
        2. Determines required capabilities
        3. Creates a specialized DynamicAgent
        4. Executes the task
        """
        state = self._ensure_state(state)

        try:
            user_message = state.metadata.get("user_message", "")
            if not user_message:
                user_message = f"Help me with {state.intent}"

            result = await self.meta_agent.execute(user_message, state, stream=False)

            if isinstance(result, AgentResult):
                state.agent_logs.append(
                    {
                        "agent": "meta_agent",
                        "status": result.status,
                        "duration_ms": result.duration_ms,
                        "error": result.error_message,
                        "output_summary": result.output_summary,
                    }
                )

                if result.action_proposals:
                    state.action_proposals.extend(result.action_proposals)

                if result.metadata_updates:
                    for update in result.metadata_updates:
                        if "meta_analysis" in update:
                            state.metadata.update(update)

                if result.status == "error":
                    state.errors.append({"agent": "meta_agent", "error": result.error_message})
            else:
                state.errors.append({"agent": "meta_agent", "error": "Unexpected result type"})

        except Exception as e:
            logger.error(f"MetaAgent node failed: {e}")
            state.errors.append({"agent": "meta_agent", "error": str(e)})

        return self._state_to_dict(state)

    async def _action_executor_node(self, state) -> dict:
        """Execute approved actions."""
        state = self._ensure_state(state)

        try:
            action_executor = ActionExecutor()
            pending_proposals = [p for p in state.action_proposals if p.get("status") == "pending"]

            logger.info(f"Executing {len(pending_proposals)} pending actions")

            for proposal_dict in pending_proposals:
                proposal = ActionProposal(**proposal_dict)

                result = await action_executor.execute(proposal)

                proposal.status = "executed" if result.success else "failed"
                proposal.execution_log_id = result.execution_log_id if result.success else None

                for i, p in enumerate(state.action_proposals):
                    if p.get("id") == proposal.id:
                        state.action_proposals[i] = proposal.dict()
                        break

            state.agent_logs.append(
                {
                    "agent": "action_executor",
                    "status": "success",
                    "duration_ms": 0,
                    "executed_actions": len(pending_proposals),
                }
            )

        except Exception as e:
            logger.error(f"Action executor failed: {e}")
            state.errors.append({"agent": "action_executor", "error": str(e)})

        return self._state_to_dict(state)

    async def orchestrate(
        self,
        context: AgentContext,
        db: Session = None,
        thread_id: str = None,
        interrupt: bool = True,
    ) -> OrchestrationResult:
        """
        Orchestrate agent execution.

        Args:
            context: Execution context
            db: Optional database session
            thread_id: Optional thread ID for checkpointing
            interrupt: Whether to interrupt before action execution

        Returns:
            OrchestrationResult
        """
        start_time = datetime.now()

        config = {"configurable": {"thread_id": thread_id or "default"}}

        initial_state = OpsAgentState(
            user_id=context.user_id,
            intent=context.intent,
            items=context.items,
            action_proposals=context.action_proposals,
            user_preferences=context.user_preferences,
            weather_context=context.weather_context,
            metadata=context.metadata,
            agent_logs=[],
            errors=[],
        )

        try:
            result_state = await self.workflow.ainvoke(self._state_to_dict(initial_state), config)

            final_state = self._ensure_state(result_state)

            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            status = "success"
            if final_state.errors:
                status = "partial_failure" if final_state.agent_logs else "failure"

            return OrchestrationResult(
                status=status,
                results={"meta_agent": self._extract_meta_result(final_state)},
                execution_time_ms=execution_time,
                error="; ".join(e.get("error", "") for e in final_state.errors) if final_state.errors else None,
            )

        except Exception as e:
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"Orchestration failed: {e}")
            return OrchestrationResult(
                status="failure",
                results={},
                execution_time_ms=execution_time,
                error=str(e),
            )

    def _extract_meta_result(self, state: OpsAgentState) -> AgentResult:
        """Extract result from final state."""
        meta_log = next((log for log in state.agent_logs if log.get("agent") == "meta_agent"), {})

        return AgentResult(
            agent_name="meta_agent",
            status=meta_log.get("status", "success"),
            output_summary=meta_log.get("output_summary", {}),
            action_proposals=state.action_proposals,
            metadata_updates=[state.metadata],
            error_message=meta_log.get("error"),
            duration_ms=meta_log.get("duration_ms", 0),
        )

    def get_meta_agent(self) -> MetaAgent:
        """Get the MetaAgent instance."""
        return self.meta_agent

    def get_tool_registry(self) -> ToolRegistry:
        """Get the tool registry."""
        return self.tool_registry

    def __repr__(self) -> str:
        return f"Orchestrator(tools={len(self.tool_registry)}, meta_agent={self.meta_agent is not None})"
