"""
Tests for DAGExecutor parallel execution engine.

Tests cover:
1. Parallel execution (independent tools run concurrently)
2. Dependency management (tools wait for dependencies)
3. Error handling and retry logic
4. Timeout handling
5. Progress event emission
"""

import asyncio
import pytest
import time
from typing import Dict, Any

from orchestrator.execution.dag_executor import (
    DAGExecutor,
    ExecutionStep,
    StepStatus,
)


# Mock tools for testing
async def mock_fast_tool(**kwargs) -> Dict[str, Any]:
    """Fast tool that completes in 0.1s."""
    await asyncio.sleep(0.1)
    return {"result": "fast_complete", "args": kwargs}


async def mock_slow_tool(**kwargs) -> Dict[str, Any]:
    """Slow tool that completes in 0.5s."""
    await asyncio.sleep(0.5)
    return {"result": "slow_complete", "args": kwargs}


async def mock_failing_tool(**kwargs) -> Dict[str, Any]:
    """Tool that always fails."""
    raise Exception("Simulated failure")


async def mock_timeout_tool(**kwargs) -> Dict[str, Any]:
    """Tool that times out."""
    await asyncio.sleep(10)  # Will timeout before completing
    return {"result": "should_not_reach"}


async def mock_flaky_tool(**kwargs) -> Dict[str, Any]:
    """Tool that fails once then succeeds."""
    if not hasattr(mock_flaky_tool, "_attempts"):
        mock_flaky_tool._attempts = 0

    mock_flaky_tool._attempts += 1

    if mock_flaky_tool._attempts == 1:
        raise Exception("First attempt fails")

    return {"result": "success_after_retry", "attempts": mock_flaky_tool._attempts}


@pytest.mark.asyncio
async def test_parallel_execution_speed():
    """
    Test that independent tools run in parallel.

    3 tools that each take 0.5s should complete in ~0.5s total (not 1.5s).
    """
    executor = DAGExecutor()

    steps = [
        ExecutionStep(tool_name="tool1", tool=mock_slow_tool, args={"id": 1}),
        ExecutionStep(tool_name="tool2", tool=mock_slow_tool, args={"id": 2}),
        ExecutionStep(tool_name="tool3", tool=mock_slow_tool, args={"id": 3}),
    ]

    start = time.time()
    result = await executor.execute_plan(steps, emit_progress=False)
    duration = time.time() - start

    # Should complete in ~0.5s (parallel) not ~1.5s (sequential)
    assert duration < 0.8, f"Expected parallel execution (~0.5s), got {duration}s"
    assert result.success is True
    assert len(result.results) == 3

    print(f"* Parallel execution: 3 tools in {duration:.2f}s (expected ~0.5s)")


@pytest.mark.asyncio
async def test_dependency_execution_order():
    """
    Test that tools wait for their dependencies.

    tool2 depends on tool1, tool3 depends on tool2.
    Should execute in order: tool1 -> tool2 -> tool3
    """
    executor = DAGExecutor()

    execution_order = []

    def make_tracked_tool(name: str):
        async def tool(**kwargs):
            execution_order.append(name)
            await asyncio.sleep(0.1)
            return {"result": f"{name}_complete"}

        return tool

    steps = [
        ExecutionStep(
            tool_name="tool3",
            tool=make_tracked_tool("tool3"),
            dependencies=["tool2"],
        ),
        ExecutionStep(
            tool_name="tool1",
            tool=make_tracked_tool("tool1"),
            dependencies=[],
        ),
        ExecutionStep(
            tool_name="tool2",
            tool=make_tracked_tool("tool2"),
            dependencies=["tool1"],
        ),
    ]

    result = await executor.execute_plan(steps, emit_progress=False)

    assert result.success is True
    assert execution_order == ["tool1", "tool2", "tool3"]

    print(f"* Dependency order: {' -> '.join(execution_order)}")


@pytest.mark.asyncio
async def test_mixed_parallel_and_dependencies():
    """
    Test complex DAG with both parallel and sequential execution.

    Structure:
        tool1 (0.1s)  tool2 (0.1s)  <- Parallel
              \\      /
               tool3 (0.1s)         <- Waits for both

    Should take ~0.2s total (not 0.3s sequential).
    """
    executor = DAGExecutor()

    steps = [
        ExecutionStep(tool_name="tool1", tool=mock_fast_tool, dependencies=[]),
        ExecutionStep(tool_name="tool2", tool=mock_fast_tool, dependencies=[]),
        ExecutionStep(tool_name="tool3", tool=mock_fast_tool, dependencies=["tool1", "tool2"]),
    ]

    start = time.time()
    result = await executor.execute_plan(steps, emit_progress=False)
    duration = time.time() - start

    assert result.success is True
    assert len(result.results) == 3
    assert duration < 0.3, f"Expected ~0.2s with parallel+deps, got {duration}s"

    print(f"* Mixed execution: parallel + deps in {duration:.2f}s")


@pytest.mark.asyncio
async def test_error_handling_and_isolation():
    """
    Test that one tool failure doesn't stop other independent tools.

    tool1 fails, but tool2 and tool3 should still complete.
    """
    executor = DAGExecutor()

    steps = [
        ExecutionStep(tool_name="tool1", tool=mock_failing_tool, retry_count=0),
        ExecutionStep(tool_name="tool2", tool=mock_fast_tool),
        ExecutionStep(tool_name="tool3", tool=mock_fast_tool),
    ]

    result = await executor.execute_plan(steps, emit_progress=False)

    # Overall should fail because one tool failed
    assert result.success is False

    # But tool2 and tool3 should complete successfully
    assert "tool2" in result.results
    assert "tool3" in result.results
    assert "tool1" in result.errors

    assert result.step_details["tool1"]["status"] == "failed"
    assert result.step_details["tool2"]["status"] == "completed"
    assert result.step_details["tool3"]["status"] == "completed"

    print(f"* Error isolation: 1 failed, 2 succeeded")


@pytest.mark.asyncio
async def test_dependency_failure_skips_dependents():
    """
    Test that when a tool fails, its dependents are skipped.

    tool1 fails -> tool2 (depends on tool1) should be skipped.
    """
    executor = DAGExecutor()

    steps = [
        ExecutionStep(tool_name="tool1", tool=mock_failing_tool, retry_count=0),
        ExecutionStep(tool_name="tool2", tool=mock_fast_tool, dependencies=["tool1"]),
    ]

    result = await executor.execute_plan(steps, emit_progress=False)

    assert result.success is False
    assert "tool1" in result.errors
    assert "tool2" in result.errors
    assert result.step_details["tool2"]["status"] == "skipped"

    print(f"* Dependency failure: tool2 skipped after tool1 failed")


@pytest.mark.asyncio
async def test_retry_mechanism():
    """
    Test that tools retry on failure with exponential backoff.

    Flaky tool fails once, then succeeds on retry.
    """
    # Reset flaky tool state
    if hasattr(mock_flaky_tool, "_attempts"):
        delattr(mock_flaky_tool, "_attempts")

    executor = DAGExecutor(retry_delay_ms=100)

    steps = [
        ExecutionStep(
            tool_name="flaky",
            tool=mock_flaky_tool,
            retry_count=2,
        ),
    ]

    result = await executor.execute_plan(steps, emit_progress=False)

    assert result.success is True
    assert result.results["flaky"]["attempts"] == 2  # Failed once, succeeded on retry
    assert result.step_details["flaky"]["attempts"] == 2

    print(f"* Retry: succeeded after {result.results['flaky']['attempts']} attempts")


@pytest.mark.asyncio
async def test_timeout_handling():
    """
    Test that tools timeout correctly.
    """
    executor = DAGExecutor()

    steps = [
        ExecutionStep(
            tool_name="timeout_tool",
            tool=mock_timeout_tool,
            timeout_ms=200,  # 0.2s timeout (tool takes 10s)
            retry_count=0,
        ),
    ]

    result = await executor.execute_plan(steps, emit_progress=False)

    assert result.success is False
    assert "timeout_tool" in result.errors
    assert "Timeout" in result.errors["timeout_tool"]

    print(f"* Timeout: tool timed out after 200ms")


@pytest.mark.asyncio
async def test_priority_execution_order():
    """
    Test that higher priority tools run first when multiple are ready.
    """
    executor = DAGExecutor(max_parallel=1)  # Force sequential to test priority

    execution_order = []

    def make_tracked_tool(name: str):
        async def tool(**kwargs):
            execution_order.append(name)
            await asyncio.sleep(0.05)
            return {"result": f"{name}_complete"}

        return tool

    steps = [
        ExecutionStep(
            tool_name="low_priority",
            tool=make_tracked_tool("low_priority"),
            priority=1,
        ),
        ExecutionStep(
            tool_name="high_priority",
            tool=make_tracked_tool("high_priority"),
            priority=10,
        ),
        ExecutionStep(
            tool_name="medium_priority",
            tool=make_tracked_tool("medium_priority"),
            priority=5,
        ),
    ]

    result = await executor.execute_plan(steps, emit_progress=False)

    assert result.success is True
    assert execution_order == ["high_priority", "medium_priority", "low_priority"]

    print(f"* Priority order: {' -> '.join(execution_order)}")


@pytest.mark.asyncio
async def test_from_tool_plan_conversion():
    """
    Test conversion from ToolPlan with parallel_groups to ExecutionSteps.
    """
    from orchestrator.agents.query_analyzer import ToolPlan

    # Mock tool plan with 2 parallel groups
    # Group 1: tool1, tool2 (parallel)
    # Group 2: tool3 (depends on both tool1 and tool2)
    tool_plan = ToolPlan(
        tools=["tool1", "tool2", "tool3"],
        parallel_groups=[
            ["tool1", "tool2"],  # First group runs in parallel
            ["tool3"],  # Second group waits for first
        ],
        reasoning="Test plan",
        expected_synthesis="Combine results",
    )

    tool_map = {
        "tool1": mock_fast_tool,
        "tool2": mock_fast_tool,
        "tool3": mock_fast_tool,
    }

    steps = DAGExecutor.from_tool_plan(tool_plan, tool_map)

    # Verify structure
    assert len(steps) == 3

    tool1_step = next(s for s in steps if s.tool_name == "tool1")
    tool2_step = next(s for s in steps if s.tool_name == "tool2")
    tool3_step = next(s for s in steps if s.tool_name == "tool3")

    # tool1 and tool2 have no dependencies (parallel)
    assert tool1_step.dependencies == []
    assert tool2_step.dependencies == []

    # tool3 depends on both tool1 and tool2
    assert set(tool3_step.dependencies) == {"tool1", "tool2"}

    # Priorities should decrease with group index
    assert tool1_step.priority > tool3_step.priority

    print(f"* ToolPlan conversion: {len(steps)} steps with correct dependencies")


if __name__ == "__main__":
    """Run tests manually for quick validation."""
    import sys

    async def run_all_tests():
        print("\n=== DAGExecutor Test Suite ===\n")

        tests = [
            ("Parallel Execution Speed", test_parallel_execution_speed),
            ("Dependency Order", test_dependency_execution_order),
            ("Mixed Parallel+Deps", test_mixed_parallel_and_dependencies),
            ("Error Isolation", test_error_handling_and_isolation),
            ("Dependency Failure", test_dependency_failure_skips_dependents),
            ("Retry Mechanism", test_retry_mechanism),
            ("Timeout Handling", test_timeout_handling),
            ("Priority Order", test_priority_execution_order),
            ("ToolPlan Conversion", test_from_tool_plan_conversion),
        ]

        passed = 0
        failed = 0

        for name, test_func in tests:
            try:
                await test_func()
                passed += 1
            except Exception as e:
                print(f"x {name}: {e}")
                failed += 1

        print(f"\n=== Results: {passed} passed, {failed} failed ===\n")

        return failed == 0

    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
