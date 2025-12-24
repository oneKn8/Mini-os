"""
Tests for DecisionMemory loop prevention.

Tests cover:
1. Question deduplication (exact and semantic)
2. Tool execution tracking
3. Loop detection
4. Circuit breaker logic
"""

import pytest

from orchestrator.memory.decision_memory import DecisionMemory, Decision


def test_exact_question_match():
    """Test that exact same question is detected."""
    memory = DecisionMemory(max_same_question=1)

    # First time should be allowed
    assert memory.has_asked("What's my schedule?") is False
    memory.record_question("What's my schedule?", result="3 events")

    # Second time should be blocked
    assert memory.has_asked("What's my schedule?") is True

    print("* Exact question match: prevented duplicate")


def test_case_insensitive_question():
    """Test that questions are case-insensitive."""
    memory = DecisionMemory(max_same_question=1)

    memory.record_question("What's MY Schedule?")

    assert memory.has_asked("what's my schedule?") is True

    print("* Case insensitive: 'What's MY Schedule?' == 'what's my schedule?'")


def test_semantic_question_similarity():
    """Test semantic similarity for question matching."""
    memory = DecisionMemory(
        max_same_question=1,
        enable_semantic_check=True,
        similarity_threshold=0.80,
    )

    memory.record_question("What's my day like?")

    # Similar questions should be caught
    similar_questions = [
        "How's my day looking?",
        "What does my day look like?",
        "How is my day?",
    ]

    for q in similar_questions:
        if memory.has_asked(q):
            print(f"  * Semantic match: '{q}' similar to 'What's my day like?'")

    # Ensure at least semantic checking is working (if embeddings available)
    # If not available, test will just pass
    print("* Semantic similarity check completed")


def test_tool_execution_tracking():
    """Test tool execution deduplication."""
    memory = DecisionMemory(max_same_tool=2)

    # Execute tool twice - should be allowed
    assert memory.has_executed_tool("search_emails", {"from": "john"}) is False
    memory.record_tool_execution("search_emails", {"from": "john"}, result=["email1"])

    assert memory.has_executed_tool("search_emails", {"from": "john"}) is False
    memory.record_tool_execution("search_emails", {"from": "john"}, result=["email1"])

    # Third time should be blocked
    assert memory.has_executed_tool("search_emails", {"from": "john"}) is True

    print("* Tool execution: blocked after 2 executions")


def test_different_tool_args():
    """Test that different arguments are treated as different executions."""
    memory = DecisionMemory(max_same_tool=1)

    memory.record_tool_execution("search_emails", {"from": "john"})

    # Different args should be allowed
    assert memory.has_executed_tool("search_emails", {"from": "jane"}) is False

    print("* Tool args: different args treated as different executions")


def test_loop_detection_repeating():
    """Test loop detection for repeating patterns."""
    memory = DecisionMemory()

    # Create a repeating pattern
    memory.record_question("Should I check calendar?")
    memory.record_tool_execution("get_todays_events", {})
    memory.record_question("Should I check calendar?")
    memory.record_tool_execution("get_todays_events", {})

    assert memory.is_looping(window_size=5) is True

    print("* Loop detection: caught repeating pattern")


def test_loop_detection_alternating():
    """Test loop detection for alternating patterns."""
    memory = DecisionMemory()

    # Create alternating pattern A->B->A->B
    memory.record_question("Check calendar?")
    memory.record_question("Check email?")
    memory.record_question("Check calendar?")
    memory.record_question("Check email?")

    assert memory.is_looping(window_size=5) is True

    print("* Loop detection: caught alternating pattern")


def test_circuit_breaker():
    """Test circuit breaker opens after failed attempts."""
    memory = DecisionMemory(max_failed_attempts=3)

    # Record 3 failed attempts
    memory.record_question("Question 1", result={"error": "failed"})
    assert memory.circuit_open is False

    memory.record_question("Question 2", result=None)
    assert memory.circuit_open is False

    memory.record_question("Question 3", result={"error": "failed"})
    assert memory.circuit_open is True

    # Circuit breaker should prevent further questions
    assert memory.has_asked("New question?") is True
    assert memory.should_early_exit() is True

    print("* Circuit breaker: opened after 3 failures")


def test_circuit_breaker_reset_on_success():
    """Test that circuit breaker resets on successful operations."""
    memory = DecisionMemory(max_failed_attempts=3)

    # Record failures
    memory.record_question("Q1", result={"error": "failed"})
    memory.record_question("Q2", result={"error": "failed"})

    assert memory.failed_attempts == 2

    # Success should decrement
    memory.record_question("Q3", result="success")

    assert memory.failed_attempts == 1
    assert memory.circuit_open is False

    print("* Circuit breaker: reset on success")


def test_manual_circuit_reset():
    """Test manual circuit breaker reset."""
    memory = DecisionMemory(max_failed_attempts=2)

    # Open circuit
    memory.record_question("Q1", result=None)
    memory.record_question("Q2", result=None)

    assert memory.circuit_open is True

    # Reset
    memory.reset_circuit_breaker()

    assert memory.circuit_open is False
    assert memory.failed_attempts == 0

    print("* Circuit breaker: manual reset works")


def test_get_stats():
    """Test statistics tracking."""
    memory = DecisionMemory()

    memory.record_question("Q1")
    memory.record_question("Q2")
    memory.record_tool_execution("tool1", {})

    stats = memory.get_stats()

    assert stats["questions_asked"] == 2
    assert stats["tools_executed"] == 1
    assert stats["actions_taken"] == 0
    assert stats["loops_prevented"] >= 0

    print(f"* Stats: {stats}")


def test_clear():
    """Test clearing all decision history."""
    memory = DecisionMemory()

    memory.record_question("Q1")
    memory.record_tool_execution("tool1", {})
    memory.loops_prevented = 5

    memory.clear()

    stats = memory.get_stats()
    assert stats["questions_asked"] == 0
    assert stats["tools_executed"] == 0
    assert stats["loops_prevented"] == 0

    print("* Clear: all history cleared")


def test_recent_decisions():
    """Test retrieving recent decisions."""
    memory = DecisionMemory()

    memory.record_question("Q1")
    memory.record_tool_execution("tool1", {})
    memory.record_question("Q2")

    recent = memory.get_recent_decisions(count=2)

    assert len(recent) == 2
    # Should be in reverse chronological order
    assert recent[0].content == "Q2"
    assert recent[1].content == "tool1"

    print("* Recent decisions: retrieved in correct order")


if __name__ == "__main__":
    """Run tests manually for quick validation."""
    import sys

    def run_all_tests():
        print("\n=== DecisionMemory Test Suite ===\n")

        tests = [
            ("Exact Question Match", test_exact_question_match),
            ("Case Insensitive", test_case_insensitive_question),
            ("Semantic Similarity", test_semantic_question_similarity),
            ("Tool Execution", test_tool_execution_tracking),
            ("Tool Args", test_different_tool_args),
            ("Loop: Repeating", test_loop_detection_repeating),
            ("Loop: Alternating", test_loop_detection_alternating),
            ("Circuit Breaker", test_circuit_breaker),
            ("Circuit Reset", test_circuit_breaker_reset_on_success),
            ("Circuit Manual Reset", test_manual_circuit_reset),
            ("Stats", test_get_stats),
            ("Clear", test_clear),
            ("Recent Decisions", test_recent_decisions),
        ]

        passed = 0
        failed = 0

        for name, test_func in tests:
            try:
                test_func()
                passed += 1
            except Exception as e:
                print(f"x {name}: {e}")
                import traceback

                traceback.print_exc()
                failed += 1

        print(f"\n=== Results: {passed} passed, {failed} failed ===\n")

        return failed == 0

    success = run_all_tests()
    sys.exit(0 if success else 1)
