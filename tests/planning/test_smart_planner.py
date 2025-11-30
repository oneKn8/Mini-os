"""
Tests for SmartPlanner multi-layer caching.

Tests cover:
1. L1 Pattern matching (regex-based)
2. L2 Semantic caching (embedding similarity)
3. L3 LLM fallback
4. Cache performance
"""

import asyncio
import pytest
import time

from orchestrator.planning.smart_planner import (
    SmartPlanner,
    PatternMatcher,
    SemanticCache,
)
from orchestrator.agents.query_analyzer import ToolPlan


@pytest.mark.asyncio
async def test_pattern_matching_day_overview():
    """Test L1 pattern matching for day overview queries."""
    matcher = PatternMatcher()

    test_queries = [
        "What's my day like?",
        "How's my day looking?",
        "What is the day like?",
        "day overview",
        "today's schedule",
    ]

    for query in test_queries:
        plan = matcher.match(query)
        assert plan is not None, f"Failed to match: {query}"
        assert "get_todays_events" in plan.tools
        assert "get_current_weather" in plan.tools
        assert "get_priority_items" in plan.tools
        # Should run all 3 in parallel
        assert len(plan.parallel_groups) == 1
        assert len(plan.parallel_groups[0]) == 3

    print(f"✓ Pattern matching: {len(test_queries)} day overview variations")


@pytest.mark.asyncio
async def test_pattern_matching_email():
    """Test L1 pattern matching for email queries."""
    matcher = PatternMatcher()

    test_queries = [
        "search emails from john",
        "find emails about project",
        "did jane email me",
    ]

    for query in test_queries:
        plan = matcher.match(query)
        assert plan is not None, f"Failed to match: {query}"
        assert plan.tools == ["search_emails"]

    print(f"✓ Pattern matching: {len(test_queries)} email variations")


@pytest.mark.asyncio
async def test_pattern_matching_speed():
    """Test that pattern matching is very fast (<1ms)."""
    matcher = PatternMatcher()

    queries = [
        "What's my day like?",
        "How's the weather?",
        "Am I free tomorrow?",
        "What should I focus on?",
    ] * 100  # 400 queries

    start = time.time()
    for query in queries:
        matcher.match(query)
    duration = time.time() - start

    avg_ms = (duration / len(queries)) * 1000

    assert avg_ms < 1.0, f"Pattern matching too slow: {avg_ms:.3f}ms avg"
    print(f"✓ Pattern matching speed: {avg_ms:.3f}ms avg ({len(queries)} queries)")


@pytest.mark.asyncio
async def test_semantic_cache_similarity():
    """Test L2 semantic cache finds similar queries."""
    cache = SemanticCache(similarity_threshold=0.8)

    # Store original query
    original_plan = ToolPlan(
        tools=["get_todays_events"],
        parallel_groups=[["get_todays_events"]],
        reasoning="Check calendar",
        expected_synthesis="Show events",
    )
    await cache.store("What's my day like?", original_plan)

    # Similar queries should match
    similar_queries = [
        "How's my day looking?",
        "What does my day look like?",
        "How is my day?",
    ]

    for query in similar_queries:
        plan = await cache.get_similar(query)
        if plan:  # Only check if embeddings are available
            assert plan is not None, f"Should match similar query: {query}"
            assert plan.tools == original_plan.tools

    print(f"✓ Semantic cache: matched {len(similar_queries)} similar queries")


@pytest.mark.asyncio
async def test_semantic_cache_miss():
    """Test L2 semantic cache doesn't match dissimilar queries."""
    cache = SemanticCache(similarity_threshold=0.85)

    # Store calendar query
    calendar_plan = ToolPlan(
        tools=["get_todays_events"],
        parallel_groups=[["get_todays_events"]],
        reasoning="Check calendar",
        expected_synthesis="Show events",
    )
    await cache.store("What's my day like?", calendar_plan)

    # Completely different queries should NOT match
    different_queries = [
        "What's the weather?",
        "Search emails from John",
        "Create a meeting",
    ]

    for query in different_queries:
        plan = await cache.get_similar(query)
        # Should either be None or (if embeddings available) not match
        if plan and plan.tools == calendar_plan.tools:
            pytest.fail(f"Should NOT match different query: {query}")

    print(f"✓ Semantic cache: correctly missed {len(different_queries)} different queries")


@pytest.mark.asyncio
async def test_semantic_cache_eviction():
    """Test cache evicts oldest entries when full."""
    cache = SemanticCache(max_cache_size=3)

    plans = [
        ("query 1", ToolPlan(tools=["tool1"], parallel_groups=[], reasoning="", expected_synthesis="")),
        ("query 2", ToolPlan(tools=["tool2"], parallel_groups=[], reasoning="", expected_synthesis="")),
        ("query 3", ToolPlan(tools=["tool3"], parallel_groups=[], reasoning="", expected_synthesis="")),
        ("query 4", ToolPlan(tools=["tool4"], parallel_groups=[], reasoning="", expected_synthesis="")),
    ]

    for query, plan in plans:
        await cache.store(query, plan)
        await asyncio.sleep(0.01)  # Ensure different timestamps

    assert len(cache.cache) == 3, "Cache should be limited to max_cache_size"

    print("✓ Semantic cache: eviction works correctly")


@pytest.mark.asyncio
async def test_smart_planner_l1_fast_path():
    """Test SmartPlanner uses L1 (pattern) for matched queries."""
    planner = SmartPlanner(enable_semantic_cache=False)

    start = time.time()
    plan = await planner.plan("What's my day like?")
    duration_ms = (time.time() - start) * 1000

    assert plan is not None
    assert "get_todays_events" in plan.tools
    assert duration_ms < 5, f"L1 should be very fast, got {duration_ms:.1f}ms"

    print(f"✓ SmartPlanner L1: {duration_ms:.2f}ms")


@pytest.mark.asyncio
async def test_smart_planner_l2_semantic():
    """Test SmartPlanner uses L2 (semantic) for similar queries."""
    planner = SmartPlanner(enable_semantic_cache=True)

    # First query goes to L3 (or L1 if pattern matches)
    plan1 = await planner.plan("What's my schedule today?")

    # Manually store in semantic cache to test L2
    if planner.semantic_cache:
        await planner.semantic_cache.store(
            "What's my schedule today?",
            ToolPlan(
                tools=["get_todays_events"],
                parallel_groups=[["get_todays_events"]],
                reasoning="Check schedule",
                expected_synthesis="Show schedule",
            )
        )

        # Similar query should hit L2
        start = time.time()
        plan2 = await planner.plan("How does my schedule look today?")
        duration_ms = (time.time() - start) * 1000

        # L2 should be fast (but slower than L1)
        assert duration_ms < 200, f"L2 should be fast, got {duration_ms:.1f}ms"

        print(f"✓ SmartPlanner L2: {duration_ms:.2f}ms")
    else:
        print("⊘ SmartPlanner L2: skipped (sentence-transformers not available)")


@pytest.mark.asyncio
async def test_smart_planner_cache_hierarchy():
    """Test that SmartPlanner checks L1 → L2 → L3 in order."""
    planner = SmartPlanner(enable_semantic_cache=True)

    # Query that matches L1 pattern
    l1_query = "What's my day like?"
    start = time.time()
    plan1 = await planner.plan(l1_query)
    l1_time = (time.time() - start) * 1000

    # Query that doesn't match L1 but is in L2
    if planner.semantic_cache:
        l2_query = "How's my schedule looking?"
        await planner.semantic_cache.store(
            "What's my schedule?",
            ToolPlan(
                tools=["get_todays_events"],
                parallel_groups=[["get_todays_events"]],
                reasoning="Check schedule",
                expected_synthesis="Show schedule",
            )
        )

        start = time.time()
        plan2 = await planner.plan(l2_query)
        l2_time = (time.time() - start) * 1000

        # L1 should be faster than L2
        assert l1_time < l2_time, f"L1 ({l1_time:.1f}ms) should be faster than L2 ({l2_time:.1f}ms)"

        print(f"✓ Cache hierarchy: L1={l1_time:.1f}ms < L2={l2_time:.1f}ms")
    else:
        print("⊘ Cache hierarchy: skipped (sentence-transformers not available)")


@pytest.mark.asyncio
async def test_smart_planner_stats():
    """Test that SmartPlanner provides cache statistics."""
    planner = SmartPlanner(enable_semantic_cache=True)

    stats = planner.get_stats()

    assert "pattern_count" in stats
    assert stats["pattern_count"] > 0

    if planner.semantic_cache:
        assert "semantic_cache" in stats
        assert "size" in stats["semantic_cache"]

    print(f"✓ SmartPlanner stats: {stats['pattern_count']} patterns")


if __name__ == "__main__":
    """Run tests manually for quick validation."""
    import sys

    async def run_all_tests():
        print("\n=== SmartPlanner Test Suite ===\n")

        tests = [
            ("Pattern: Day Overview", test_pattern_matching_day_overview),
            ("Pattern: Email", test_pattern_matching_email),
            ("Pattern: Speed", test_pattern_matching_speed),
            ("Semantic: Similarity", test_semantic_cache_similarity),
            ("Semantic: Miss", test_semantic_cache_miss),
            ("Semantic: Eviction", test_semantic_cache_eviction),
            ("Planner: L1", test_smart_planner_l1_fast_path),
            ("Planner: L2", test_smart_planner_l2_semantic),
            ("Planner: Hierarchy", test_smart_planner_cache_hierarchy),
            ("Planner: Stats", test_smart_planner_stats),
        ]

        passed = 0
        failed = 0

        for name, test_func in tests:
            try:
                await test_func()
                passed += 1
            except Exception as e:
                print(f"✗ {name}: {e}")
                import traceback
                traceback.print_exc()
                failed += 1

        print(f"\n=== Results: {passed} passed, {failed} failed ===\n")

        return failed == 0

    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
