"""
Base agent interface and context definitions.
Supports both AgentContext (legacy) and OpsAgentState (LangGraph).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union

from pydantic import BaseModel

from orchestrator.state import OpsAgentState


class AgentContext(BaseModel):
    """Context passed to agents during execution (legacy support)."""

    model_config = {"arbitrary_types_allowed": True, "protected_namespaces": ()}

    user_id: str
    intent: str  # refresh_inbox, plan_day, handle_item, etc.
    items: List[Dict] = []
    action_proposals: List[Dict] = []
    user_preferences: Dict = {}
    weather_context: Dict = {}
    metadata: Dict = {}
    # Added model override support
    model_provider: Optional[str] = None
    model_name: Optional[str] = None

    @classmethod
    def from_state(cls, state: OpsAgentState) -> "AgentContext":
        """Create AgentContext from OpsAgentState."""
        ctx = cls(
            user_id=state.user_id,
            intent=state.intent,
            items=state.items,
            action_proposals=state.action_proposals,
            user_preferences=state.user_preferences,
            weather_context=state.weather_context,
            metadata=state.metadata,
        )
        # Extract model preference from metadata if present
        if state.metadata and "model_provider" in state.metadata:
            ctx.model_provider = state.metadata.get("model_provider")
        if state.metadata and "model_name" in state.metadata:
            ctx.model_name = state.metadata.get("model_name")
        return ctx


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
    """Base class for all agents. Supports both AgentContext and OpsAgentState."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def run(self, context: Union[AgentContext, OpsAgentState]) -> AgentResult:
        """
        Execute agent logic.

        Args:
            context: Execution context (AgentContext or OpsAgentState)

        Returns:
            AgentResult with outputs and proposals
        """
        pass

    def _get_context(self, input_data: Union[AgentContext, OpsAgentState]) -> AgentContext:
        """Convert input to AgentContext for compatibility."""
        if isinstance(input_data, OpsAgentState):
            return AgentContext.from_state(input_data)
        return input_data

    def _update_state_from_result(self, state: OpsAgentState, result: AgentResult) -> OpsAgentState:
        """Update LangGraph state with agent result."""
        # Add agent log with output_summary for result reconstruction
        state.agent_logs.append(
            {
                "agent": self.name,
                "status": result.status,
                "duration_ms": result.duration_ms,
                "error": result.error_message,
                "output_summary": result.output_summary,
            }
        )

        # Add action proposals
        if result.action_proposals:
            state.action_proposals.extend(result.action_proposals)

        # Update metadata
        if result.metadata_updates:
            for update in result.metadata_updates:
                if "item_id" in update:
                    # Find item in state and update its metadata
                    item_id = update["item_id"]
                    for item in state.items:
                        if item.get("id") == item_id:
                            if "metadata" not in item:
                                item["metadata"] = {}
                            item["metadata"].update(update["metadata"])
                else:
                    state.metadata.update(update)

        # Add errors
        if result.status == "error":
            state.errors.append({"agent": self.name, "error": result.error_message})

        return state

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
