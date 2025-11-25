"""
Multi-agent orchestrator using LangGraph.
Based on the pattern from GenerativeAIExamples smart-health-agent.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from langgraph.graph import END, StateGraph

from orchestrator.agents.base import AgentContext, AgentResult, BaseAgent
from orchestrator.agents.email_agent import EmailAgent
from orchestrator.agents.event_agent import EventAgent
from orchestrator.agents.planner_agent import PlannerAgent
from orchestrator.agents.preference_agent import PreferenceAgent
from orchestrator.agents.safety_agent import SafetyAgent
from orchestrator.agents.triage_agent import TriageAgent
from orchestrator.registry import AgentRegistry
from orchestrator.state import OpsAgentState

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationResult:
    """Result from orchestrating multiple agents."""

    status: str  # success, partial_failure, failure
    results: Dict[str, AgentResult]
    execution_time_ms: int
    error: str = None


class Orchestrator:
    """Orchestrates execution of multiple agents using LangGraph."""

    def __init__(self):
        self.registry = AgentRegistry()
        self._register_default_agents()
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow for multi-agent orchestration."""
        workflow = StateGraph(OpsAgentState)

        # Add agent nodes
        workflow.add_node("triage", self._triage_node)
        workflow.add_node("safety", self._safety_node)
        workflow.add_node("email", self._email_node)
        workflow.add_node("event", self._event_node)
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("preference", self._preference_node)

        # Define workflow edges based on intent
        workflow.set_entry_point("triage")

        # For refresh_inbox: triage -> safety -> email -> event -> END
        workflow.add_conditional_edges(
            "triage",
            self._route_after_triage,
            {
                "safety": "safety",
                "email": "email",
                "event": "event",
                "planner": "planner",
                "preference": "preference",
                "end": END,
            },
        )

        workflow.add_edge("safety", "email")
        workflow.add_edge("email", "event")
        workflow.add_edge("event", END)
        workflow.add_edge("planner", END)
        workflow.add_edge("preference", END)

        return workflow.compile()

    def _route_after_triage(self, state: OpsAgentState) -> str:
        """Route to next agent based on intent."""
        intent = state.intent
        if intent == "refresh_inbox":
            return "safety"
        elif intent == "plan_day":
            return "planner"
        elif intent == "learn_preferences":
            return "preference"
        else:
            return "end"

    async def _triage_node(self, state: OpsAgentState) -> OpsAgentState:
        """Triage agent node."""
        agent = self.registry.get("triage")
        if not agent:
            state.errors.append({"agent": "triage", "error": "Agent not found"})
            return state

        # Pass state directly - agent will handle conversion if needed
        result = await agent.run(state)
        return agent._update_state_from_result(state, result)

    async def _safety_node(self, state: OpsAgentState) -> OpsAgentState:
        """Safety agent node."""
        agent = self.registry.get("safety")
        if not agent:
            state.errors.append({"agent": "safety", "error": "Agent not found"})
            return state

        result = await agent.run(state)
        return agent._update_state_from_result(state, result)

    async def _email_node(self, state: OpsAgentState) -> OpsAgentState:
        """Email agent node."""
        agent = self.registry.get("email")
        if not agent:
            state.errors.append({"agent": "email", "error": "Agent not found"})
            return state

        result = await agent.run(state)
        return agent._update_state_from_result(state, result)

    async def _event_node(self, state: OpsAgentState) -> OpsAgentState:
        """Event agent node."""
        agent = self.registry.get("event")
        if not agent:
            state.errors.append({"agent": "event", "error": "Agent not found"})
            return state

        result = await agent.run(state)
        return agent._update_state_from_result(state, result)

    async def _planner_node(self, state: OpsAgentState) -> OpsAgentState:
        """Planner agent node."""
        agent = self.registry.get("planner")
        if not agent:
            state.errors.append({"agent": "planner", "error": "Agent not found"})
            return state

        result = await agent.run(state)
        return agent._update_state_from_result(state, result)

    async def _preference_node(self, state: OpsAgentState) -> OpsAgentState:
        """Preference agent node."""
        agent = self.registry.get("preference")
        if not agent:
            state.errors.append({"agent": "preference", "error": "Agent not found"})
            return state

        result = await agent.run(state)
        return agent._update_state_from_result(state, result)

    async def run(self, intent: str, context: AgentContext) -> OrchestrationResult:
        """Execute LangGraph workflow for the given intent."""
        start_time = datetime.now()

        try:
            # Convert context to LangGraph state
            initial_state = OpsAgentState(
                user_id=context.user_id,
                intent=intent,
                items=context.items,
                action_proposals=context.action_proposals or [],
                user_preferences=context.user_preferences or {},
                weather_context=context.weather_context or {},
                metadata=context.metadata or {},
            )

            # Run LangGraph workflow
            final_state = await self.workflow.ainvoke(initial_state)

            # Convert state back to results format
            results = {}
            for log in final_state.agent_logs:
                agent_name = log["agent"]
                results[agent_name] = AgentResult(
                    agent_name=agent_name,
                    status=log["status"],
                    duration_ms=log["duration_ms"],
                    error_message=log.get("error"),
                    action_proposals=final_state.action_proposals,
                )

            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            status = "success" if not final_state.errors else "partial_failure"
            return OrchestrationResult(
                status=status,
                results=results,
                execution_time_ms=duration_ms,
                error=str(final_state.errors) if final_state.errors else None,
            )

        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"Orchestration failed: {e}", exc_info=True)
            return OrchestrationResult(status="failure", results={}, execution_time_ms=duration_ms, error=str(e))

    def build_context(self, intent: str, items: List[Dict], user_id: str) -> AgentContext:
        """Build initial context for orchestration."""
        return AgentContext(
            user_id=user_id,
            intent=intent,
            items=items,
            user_preferences={},
            weather_context={},
            metadata={},
            action_proposals=[],
        )

    def _register_default_agents(self):
        """Register built-in agents so they are available for orchestration."""
        default_agents: Dict[str, BaseAgent] = {
            "triage": TriageAgent(),
            "safety": SafetyAgent(),
            "email": EmailAgent(),
            "event": EventAgent(),
            "planner": PlannerAgent(),
            "preference": PreferenceAgent(),
        }

        for name, agent in default_agents.items():
            if not self.registry.is_registered(name):
                self.registry.register(name, agent)
