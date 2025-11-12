"""
Base agent interface and context definitions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AgentContext(BaseModel):
    """Context passed to agents during execution."""

    user_id: str
    intent: str  # refresh_inbox, plan_day, handle_item, etc.
    items: List[Dict] = []
    action_proposals: List[Dict] = []
    user_preferences: Dict = {}
    weather_context: Dict = {}
    metadata: Dict = {}

    class Config:
        arbitrary_types_allowed = True


class AgentResult(BaseModel):
    """Result returned by agent execution."""

    agent_name: str
    status: str  # success, partial, error
    output_summary: Dict = {}
    action_proposals: List[Dict] = []
    metadata_updates: List[Dict] = []
    error_message: Optional[str] = None
    duration_ms: int = 0

    class Config:
        arbitrary_types_allowed = True


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def run(self, context: AgentContext) -> AgentResult:
        """
        Execute agent logic.

        Args:
            context: Execution context with user data and preferences

        Returns:
            AgentResult with outputs and proposals
        """
        pass

    def _create_result(
        self,
        status: str = "success",
        output_summary: Dict = None,
        action_proposals: List[Dict] = None,
        metadata_updates: List[Dict] = None,
        error_message: str = None,
        duration_ms: int = 0,
    ) -> AgentResult:
        """Helper to create AgentResult."""
        return AgentResult(
            agent_name=self.name,
            status=status,
            output_summary=output_summary or {},
            action_proposals=action_proposals or [],
            metadata_updates=metadata_updates or [],
            error_message=error_message,
            duration_ms=duration_ms,
        )
