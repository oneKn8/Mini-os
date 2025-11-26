"""
Multi-agent orchestrator using LangGraph.
Based on the pattern from GenerativeAIExamples smart-health-agent.
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
from orchestrator.agents.base import AgentContext, AgentResult, BaseAgent
from orchestrator.agents.email_agent import EmailAgent
from orchestrator.agents.event_agent import EventAgent
from orchestrator.agents.planner_agent import PlannerAgent
from orchestrator.agents.preference_agent import PreferenceAgent
from orchestrator.agents.rag_agent import RAGAgent
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
        self.checkpointer = MemorySaver()
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
        workflow.add_node("rag", self._rag_node)
        workflow.add_node("action_executor", self._action_executor_node)

        # Define workflow edges based on intent
        workflow.set_entry_point("triage")

        # For refresh_inbox: triage -> safety -> email -> event -> action_executor -> END
        workflow.add_conditional_edges(
            "triage",
            self._route_after_triage,
            {
                "safety": "safety",
                "email": "email",
                "event": "event",
                "planner": "planner",
                "preference": "preference",
                "rag": "rag",
                "end": END,
            },
        )

        workflow.add_edge("safety", "email")
        workflow.add_edge("email", "event")
        workflow.add_conditional_edges(
            "event", self._route_to_executor, {"action_executor": "action_executor", "end": END}
        )

        workflow.add_conditional_edges(
            "planner", self._route_to_executor, {"action_executor": "action_executor", "end": END}
        )

        workflow.add_edge("preference", END)
        workflow.add_edge("rag", END)
        workflow.add_edge("action_executor", END)

        return workflow.compile(checkpointer=self.checkpointer, interrupt_before=["action_executor"])

    def _route_after_triage(self, state) -> str:
        """Route to next agent based on intent."""
        intent = state.get("intent") if isinstance(state, dict) else state.intent
        if intent == "refresh_inbox":
            return "safety"
        elif intent == "plan_day":
            return "planner"
        elif intent == "learn_preferences":
            return "preference"
        elif intent in ("knowledge_query", "rag_query", "ask_question"):
            return "rag"
        else:
            return "end"

    def _route_to_executor(self, state) -> str:
        """Check if there are pending actions to execute."""
        proposals = state.get("action_proposals", []) if isinstance(state, dict) else state.action_proposals
        if any(p.get("status") == "pending" for p in proposals):
            return "action_executor"
        return "end"

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
            "rag": RAGAgent(),
        }

        for name, agent in default_agents.items():
            if not self.registry.is_registered(name):
                self.registry.register(name, agent)

    def _ensure_state(self, state) -> OpsAgentState:
        """Convert dict state to OpsAgentState if needed."""
        if isinstance(state, dict):
            return OpsAgentState(**state)
        return state

    def _state_to_dict(self, state: OpsAgentState) -> dict:
        """Convert OpsAgentState to dict for LangGraph."""
        return state.model_dump()

    async def _triage_node(self, state) -> dict:
        """Triage agent node."""
        state = self._ensure_state(state)
        agent = self.registry.get("triage")
        if not agent:
            state.errors.append({"agent": "triage", "error": "Agent not found"})
            return self._state_to_dict(state)

        result = await agent.run(state)
        updated = agent._update_state_from_result(state, result)
        return self._state_to_dict(updated)

    async def _safety_node(self, state) -> dict:
        """Safety agent node."""
        state = self._ensure_state(state)
        agent = self.registry.get("safety")
        if not agent:
            state.errors.append({"agent": "safety", "error": "Agent not found"})
            return self._state_to_dict(state)

        result = await agent.run(state)
        updated = agent._update_state_from_result(state, result)
        return self._state_to_dict(updated)

    async def _email_node(self, state) -> dict:
        """Email agent node."""
        state = self._ensure_state(state)
        agent = self.registry.get("email")
        if not agent:
            state.errors.append({"agent": "email", "error": "Agent not found"})
            return self._state_to_dict(state)

        result = await agent.run(state)
        updated = agent._update_state_from_result(state, result)
        return self._state_to_dict(updated)

    async def _event_node(self, state) -> dict:
        """Event agent node."""
        state = self._ensure_state(state)
        agent = self.registry.get("event")
        if not agent:
            state.errors.append({"agent": "event", "error": "Agent not found"})
            return self._state_to_dict(state)

        result = await agent.run(state)
        updated = agent._update_state_from_result(state, result)
        return self._state_to_dict(updated)

    async def _planner_node(self, state) -> dict:
        """Planner agent node."""
        state = self._ensure_state(state)
        agent = self.registry.get("planner")
        if not agent:
            state.errors.append({"agent": "planner", "error": "Agent not found"})
            return self._state_to_dict(state)

        result = await agent.run(state)
        updated = agent._update_state_from_result(state, result)
        return self._state_to_dict(updated)

    async def _preference_node(self, state) -> dict:
        """Preference agent node."""
        state = self._ensure_state(state)
        agent = self.registry.get("preference")
        if not agent:
            state.errors.append({"agent": "preference", "error": "Agent not found"})
            return self._state_to_dict(state)

        result = await agent.run(state)
        updated = agent._update_state_from_result(state, result)
        return self._state_to_dict(updated)

    async def _rag_node(self, state) -> dict:
        """RAG agent node for knowledge retrieval and question answering."""
        state = self._ensure_state(state)
        agent = self.registry.get("rag")
        if not agent:
            state.errors.append({"agent": "rag", "error": "Agent not found"})
            return self._state_to_dict(state)

        result = await agent.run(state)
        updated = agent._update_state_from_result(state, result)
        return self._state_to_dict(updated)

    async def _action_executor_node(self, state, config) -> dict:
        """Execute approved actions."""
        state = self._ensure_state(state)
        db = config.get("configurable", {}).get("db")

        if not db:
            logger.warning("No database session provided to action executor")
            return self._state_to_dict(state)

        executor = ActionExecutor(db)

        # Execute actions that are approved (or we assume approved if we passed the interrupt)
        # In a real scenario, we'd check for 'approved' status.
        # For this MVP, we assume if we resumed, we are good to go, OR we check DB status.

        executed_count = 0
        for proposal_dict in state.action_proposals:
            # We check if the DB record is 'approved' (set by the API before resuming)
            # OR if it's 'pending', we assume the user approved it by resuming?
            # Better to be safe: only execute 'approved' ones.

            # Fetch from DB
            p_id = proposal_dict.get("id")
            if not p_id:
                continue

            proposal = db.query(ActionProposal).filter(ActionProposal.id == p_id).first()
            if proposal and proposal.status == "approved":
                try:
                    executor.execute(proposal)
                    executed_count += 1
                    # Update state dict to reflect execution
                    proposal_dict["status"] = "executed"
                except Exception as e:
                    logger.error(f"Failed to execute proposal {p_id}: {e}")
                    proposal_dict["status"] = "failed"

        if executed_count > 0:
            state.agent_logs.append(
                {
                    "agent": "action_executor",
                    "status": "success",
                    "output_summary": {"executed": executed_count},
                    "duration_ms": 0,
                }
            )

        return self._state_to_dict(state)

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

            # Run LangGraph workflow - pass as dict
            # Note: 'run' doesn't support HITL/checkpoints well since it's one-shot.
            # It will stop at interrupt.
            final_state = await self.workflow.ainvoke(
                initial_state.model_dump(), config={"configurable": {"thread_id": context.user_id}}
            )

            # Convert state back to results format
            # LangGraph returns AddableValuesDict, so access as dict
            results = {}
            agent_logs = (
                final_state.get("agent_logs", [])
                if isinstance(final_state, dict)
                else getattr(final_state, "agent_logs", [])
            )
            action_proposals = (
                final_state.get("action_proposals", [])
                if isinstance(final_state, dict)
                else getattr(final_state, "action_proposals", [])
            )
            errors = (
                final_state.get("errors", []) if isinstance(final_state, dict) else getattr(final_state, "errors", [])
            )

            for log in agent_logs:
                agent_name = log["agent"]
                results[agent_name] = AgentResult(
                    agent_name=agent_name,
                    status=log["status"],
                    duration_ms=log["duration_ms"],
                    error_message=log.get("error"),
                    output_summary=log.get("output_summary", {}),
                    action_proposals=action_proposals,
                )

            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            status = "success" if not errors else "partial_failure"
            return OrchestrationResult(
                status=status,
                results=results,
                execution_time_ms=duration_ms,
                error=str(errors) if errors else None,
            )

        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"Orchestration failed: {e}", exc_info=True)
            return OrchestrationResult(status="failure", results={}, execution_time_ms=duration_ms, error=str(e))

    async def stream(self, intent: str, context: AgentContext, db_session: Session = None):
        """Execute LangGraph workflow and yield events."""
        initial_state = OpsAgentState(
            user_id=context.user_id,
            intent=intent,
            items=context.items,
            action_proposals=context.action_proposals or [],
            user_preferences=context.user_preferences or {},
            weather_context=context.weather_context or {},
            metadata=context.metadata or {},
        )

        target_nodes = {"triage", "safety", "email", "event", "planner", "preference", "rag", "action_executor"}

        # Config for checkpointing and DB access
        config = {"configurable": {"thread_id": context.user_id, "db": db_session}}

        async for event in self.workflow.astream_events(initial_state.model_dump(), version="v2", config=config):
            kind = event["event"]
            name = event["name"]

            # Node Start
            if kind == "on_chain_start" and name in target_nodes:
                yield {
                    "type": "thought",
                    "agent": name,
                    "status": "running",
                    "log": {"message": f"Starting {name} agent..."},
                }

            # Node End (Success)
            elif kind == "on_chain_end" and name in target_nodes:
                output = event["data"].get("output")
                if output and isinstance(output, dict):
                    agent_logs = output.get("agent_logs", [])
                    if agent_logs:
                        latest_log = agent_logs[-1]
                        # Only yield if it matches our agent to avoid duplicate logs
                        if latest_log.get("agent") == name:
                            yield {
                                "type": "thought",
                                "agent": name,
                                "status": latest_log.get("status"),
                                "summary": latest_log.get("output_summary"),
                                "log": latest_log,
                            }

        # Check if execution stopped due to interrupt (approval needed)
        try:
            snapshot = self.workflow.get_state(config)
            if snapshot.next:
                # If the next node is action_executor, we need approval
                if "action_executor" in snapshot.next:
                    # Get pending proposals from state
                    state_values = snapshot.values
                    proposals = state_values.get("action_proposals", [])
                    pending = [p for p in proposals if p.get("status") == "pending"]

                    yield {"type": "approval_required", "agent": "action_executor", "proposals": pending}
        except Exception as e:
            logger.warning(f"Failed to check workflow state for interrupts: {e}")

    async def resume(self, user_id: str, db_session: Session = None):
        """Resume workflow execution from checkpoint after approval."""
        config = {"configurable": {"thread_id": user_id, "db": db_session}}
        target_nodes = {"triage", "safety", "email", "event", "planner", "preference", "rag", "action_executor"}

        try:
            snapshot = self.workflow.get_state(config)
            if not snapshot.next:
                logger.warning(f"No pending workflow state found for user {user_id}")
                return

            # Continue from where we left off
            async for event in self.workflow.astream_events(None, version="v2", config=config):
                kind = event["event"]
                name = event["name"]

                # Node Start
                if kind == "on_chain_start" and name in target_nodes:
                    yield {
                        "type": "thought",
                        "agent": name,
                        "status": "running",
                        "log": {"message": f"Resuming {name} agent..."},
                    }

                # Node End (Success)
                elif kind == "on_chain_end" and name in target_nodes:
                    output = event["data"].get("output")
                    if output and isinstance(output, dict):
                        agent_logs = output.get("agent_logs", [])
                        if agent_logs:
                            latest_log = agent_logs[-1]
                            if latest_log.get("agent") == name:
                                yield {
                                    "type": "thought",
                                    "agent": name,
                                    "status": latest_log.get("status"),
                                    "summary": latest_log.get("output_summary"),
                                    "log": latest_log,
                                }
        except Exception as e:
            logger.error(f"Failed to resume workflow: {e}", exc_info=True)
            yield {"type": "error", "error": f"Failed to resume workflow: {str(e)}"}
