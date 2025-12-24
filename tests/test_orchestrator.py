"""
Tests for the orchestrator
"""

import os
import pytest

from orchestrator.orchestrator import Orchestrator

# Skip all tests in this module if OPENAI_API_KEY is not set
pytestmark = pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")


@pytest.mark.asyncio
async def test_orchestrator_plan_day():
    """Test that orchestrator can run plan_day intent."""
    orchestrator = Orchestrator()

    context = orchestrator.build_context(
        intent="plan_day",
        items=[
            {"id": "1", "title": "Test email", "source_type": "email", "importance": "high"},
            {"id": "2", "title": "Test event", "source_type": "event", "importance": "medium"},
        ],
        user_id="test_user",
    )

    result = await orchestrator.run("plan_day", context)

    assert result.status in ["success", "partial_failure"]
    assert "planner" in result.results
    assert result.execution_time_ms > 0


def test_agent_sequence():
    """Test that agent sequences are correctly defined."""
    orchestrator = Orchestrator()

    assert orchestrator._get_agent_sequence("refresh_inbox") == ["triage", "safety", "email", "event"]
    assert orchestrator._get_agent_sequence("plan_day") == ["planner"]
    assert orchestrator._get_agent_sequence("unknown") == ["triage"]
