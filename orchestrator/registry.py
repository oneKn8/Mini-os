"""
Agent registry for managing agent implementations.
"""

from typing import Dict, Type

from orchestrator.agents.base import BaseAgent


class AgentRegistry:
    """Registry mapping agent names to implementations."""

    def __init__(self):
        self._agents: Dict[str, Type[BaseAgent]] = {}

    def register(self, name: str, agent_class: Type[BaseAgent]):
        """Register an agent implementation."""
        self._agents[name] = agent_class

    def get(self, name: str) -> Type[BaseAgent]:
        """Get agent class by name."""
        if name not in self._agents:
            raise ValueError(f"Agent '{name}' not registered")
        return self._agents[name]

    def list_agents(self) -> list:
        """List all registered agent names."""
        return list(self._agents.keys())

    def is_registered(self, name: str) -> bool:
        """Check if agent is registered."""
        return name in self._agents


# Global registry instance
registry = AgentRegistry()
