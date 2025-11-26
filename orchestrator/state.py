"""
LangGraph state model for multi-agent orchestration.
Based on the pattern from GenerativeAIExamples smart-health-agent.
"""

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class OpsAgentState(BaseModel):
    """State passed through LangGraph workflow for multi-agent orchestration."""

    user_id: str
    intent: str  # refresh_inbox, plan_day, handle_item, etc.
    items: List[Dict[str, Any]] = Field(default_factory=list)
    action_proposals: List[Dict[str, Any]] = Field(default_factory=list)
    agent_logs: List[Dict[str, Any]] = Field(default_factory=list)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    weather_context: Dict[str, Any] = Field(default_factory=dict)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True
