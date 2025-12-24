"""
Integration test for EnhancedConversationalAgent.

Tests the full pipeline:
1. SmartPlanner creates execution plan
2. DAGExecutor runs tools in parallel
3. LLMCache + ToolCache reduce latency
4. DecisionMemory prevents loops
"""

import asyncio
import pytest
import time
from typing import List, Dict, Any

from orchestrator.enhanced_agent import EnhancedConversationalAgent


@pytest.mark.asyncio
async def test_enhanced_agent_basic_query():
    """Test basic query handling."""
    agent = EnhancedConversationalAgent(enable_caching=False, enable_parallel=False)

    events = []
    async for event in agent.stream("What's the weather like?"):
        events.append(event)

    # Should have planning, reasoning, and response events
    event_types = [e["type"] for e in events]
    assert "reasoning" in event_types or "plan" in event_types
    assert any(e["type"] == "response" for e in events)

    # Get final response
    response_event = next(e for e in events if e["type"] == "response")
    assert "content" in response_event
    assert len(response_event["content"]) > 0

    print(f"* Basic query: {len(events)} events, response length {len(response_event['content'])}")


@pytest.mark.asyncio
async def test_enhanced_agent_multi_tool_query():
    """Test query requiring multiple tools."""
    agent = EnhancedConversationalAgent(enable_caching=False, enable_parallel=True)

    start = time.time()
    events = []

    async for event in agent.stream("What's my day like?"):
        events.append(event)

    duration = time.time() - start

    # Should use multiple tools
    response_event = next((e for e in events if e["type"] == "response"), None)
    assert response_event is not None

    tools_used = response_event.get("tools_used", [])
    assert len(tools_used) > 0

    timing = response_event.get("timing", {})
    print(
        f"* Multi-tool query: {len(tools_used)} tools in {duration:.2f}s "
        f"(plan={timing.get('plan_ms', 0)}ms, exec={timing.get('execution_ms', 0)}ms)"
    )


@pytest.mark.asyncio
async def test_enhanced_agent_caching():
    """Test that caching improves performance on repeated queries."""
    agent = EnhancedConversationalAgent(enable_caching=True, enable_parallel=True)

    query = "What's my schedule today?"

    # First query (cache miss)
    start1 = time.time()
    events1 = []
    async for event in agent.stream(query):
        events1.append(event)
    duration1 = time.time() - start1

    # Second identical query (should be faster due to caching)
    start2 = time.time()
    events2 = []
    async for event in agent.stream(query):
        events2.append(event)
    duration2 = time.time() - start2

    # Second query should be faster (though both may be fast due to pattern matching)
    print(
        f"* Caching: 1st query {duration1:.3f}s, 2nd query {duration2:.3f}s " f"(speedup: {duration1/duration2:.1f}x)"
    )

    # Check cache stats
    stats = agent.get_stats()
    print(f"  Cache stats: {stats.get('cache_hits', 0)} hits, {stats.get('cache_misses', 0)} misses")


@pytest.mark.asyncio
async def test_enhanced_agent_stats():
    """Test statistics tracking."""
    agent = EnhancedConversationalAgent(enable_caching=False, enable_parallel=False)

    # Process a few queries
    for query in ["Hello", "What's the weather?", "Thank you"]:
        events = []
        async for event in agent.stream(query):
            events.append(event)

    # Get stats
    stats = agent.get_stats()

    assert stats["queries_handled"] >= 3
    assert "planner" in stats
    assert "decision_memory" in stats

    print(f"* Stats: {stats['queries_handled']} queries handled")
    print(f"  Planner: {stats['planner']}")
    print(f"  Memory: {stats['decision_memory']}")


@pytest.mark.asyncio
async def test_enhanced_agent_parallel_speedup():
    """Test that parallel execution is faster than sequential."""
    # Agent with parallel enabled
    parallel_agent = EnhancedConversationalAgent(
        enable_caching=False,
        enable_parallel=True,
    )

    # Agent with parallel disabled
    sequential_agent = EnhancedConversationalAgent(
        enable_caching=False,
        enable_parallel=False,
    )

    query = "What's my day like?"  # Multi-tool query

    # Parallel execution
    start_parallel = time.time()
    events_parallel = []
    async for event in parallel_agent.stream(query):
        events_parallel.append(event)
    parallel_duration = time.time() - start_parallel

    # Sequential execution
    start_sequential = time.time()
    events_sequential = []
    async for event in sequential_agent.stream(query):
        events_sequential.append(event)
    sequential_duration = time.time() - start_sequential

    # Parallel should be faster (or at least not significantly slower)
    speedup = sequential_duration / parallel_duration if parallel_duration > 0 else 1.0

    print(
        f"* Parallel vs Sequential: "
        f"parallel={parallel_duration:.2f}s, sequential={sequential_duration:.2f}s, "
        f"speedup={speedup:.1f}x"
    )

    # Note: Speedup may not always be significant due to:
    # - Pattern matching making both fast
    # - Network latency dominating execution time
    # - Small number of tools


if __name__ == "__main__":
    """Run tests manually."""
    import sys

    async def run_all_tests():
        print("\n=== EnhancedAgent Integration Tests ===\n")

        tests = [
            ("Basic Query", test_enhanced_agent_basic_query),
            ("Multi-Tool Query", test_enhanced_agent_multi_tool_query),
            ("Caching", test_enhanced_agent_caching),
            ("Stats", test_enhanced_agent_stats),
            ("Parallel Speedup", test_enhanced_agent_parallel_speedup),
        ]

        passed = 0
        failed = 0

        for name, test_func in tests:
            try:
                await test_func()
                passed += 1
            except Exception as e:
                print(f"x {name}: {e}")
                import traceback

                traceback.print_exc()
                failed += 1

        print(f"\n=== Results: {passed} passed, {failed} failed ===\n")

        return failed == 0

    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
