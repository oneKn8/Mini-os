"""
Multi-agent orchestrator
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from orchestrator.agents.base import AgentContext, AgentResult, BaseAgent
from orchestrator.agents.email_agent import EmailAgent
from orchestrator.agents.event_agent import EventAgent
from orchestrator.agents.planner_agent import PlannerAgent
from orchestrator.agents.preference_agent import PreferenceAgent
from orchestrator.agents.safety_agent import SafetyAgent
from orchestrator.agents.triage_agent import TriageAgent
from orchestrator.registry import AgentRegistry

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationResult:
    """Result from orchestrating multiple agents."""

    status: str  # success, partial_failure, failure
    results: Dict[str, AgentResult]
    execution_time_ms: int
    error: str = None


class Orchestrator:
    """Orchestrates execution of multiple agents based on intent."""

    def __init__(self):
        self.registry = AgentRegistry()
        self._register_default_agents()

    async def run(self, intent: str, context: AgentContext) -> OrchestrationResult:
        """Execute agent chain for the given intent."""
        start_time = datetime.now()

        try:
            agent_sequence = self._get_agent_sequence(intent)
            results = {}

            for agent_name in agent_sequence:
                agent = self.registry.get(agent_name)

                if not agent:
                    logger.warning(f"Agent {agent_name} not found in registry")
                    continue

                logger.info(f"Running agent: {agent_name}")
                result = await agent.run(context)
                results[agent_name] = result

                if result.status == "error":
                    logger.error(f"Agent {agent_name} failed: {result.error_message}")

                self._update_context(context, result)

            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            return OrchestrationResult(status="success", results=results, execution_time_ms=duration_ms)

        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"Orchestration failed: {e}", exc_info=True)
            return OrchestrationResult(status="failure", results={}, execution_time_ms=duration_ms, error=str(e))

    def _get_agent_sequence(self, intent: str) -> List[str]:
        """Determine which agents to run based on intent."""
        sequences = {
            "refresh_inbox": ["triage", "safety", "email", "event"],
            "plan_day": ["planner"],
            "handle_item": ["triage", "email", "event"],
            "learn_preferences": ["preference"],
        }

        return sequences.get(intent, ["triage"])

    def _update_context(self, context: AgentContext, result: AgentResult):
        """Update context with agent results."""
        if result.metadata_updates:
            for update in result.metadata_updates:
                context.metadata.update(update)

        if result.action_proposals:
            if not hasattr(context, "action_proposals"):
                context.action_proposals = []
            context.action_proposals.extend(result.action_proposals)

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
