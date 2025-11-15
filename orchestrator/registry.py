"""
Agent registry for managing agent implementations.
"""

from typing import Dict, Optional

from orchestrator.agents.base import BaseAgent


class AgentRegistry:
    """Registry mapping agent names to implementations."""

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, name: str, agent: BaseAgent):
        """Register an agent implementation."""
        self._agents[name] = agent

    def get(self, name: str) -> Optional[BaseAgent]:
        """Get agent by name if registered."""
        return self._agents.get(name)

    def list_agents(self) -> list:
        """List all registered agent names."""
        return list(self._agents.keys())

    def is_registered(self, name: str) -> bool:
        """Check if agent is registered."""
        return name in self._agents


# Global registry instance
registry = AgentRegistry()
