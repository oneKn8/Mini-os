"""
Tests for ContextWindowManager with auto-compaction.
"""

import pytest

from orchestrator.context.context_window_manager import ContextWindowManager, MessageEntry


def test_new_session_fresh_context():
    """Test that new session starts with fresh 126K available."""
    manager = ContextWindowManager(max_tokens=126000)

    usage = manager.get_token_usage("session_1")

    assert usage["total_tokens"] == 0
    assert usage["available"] == 126000
    assert usage["utilization"] == 0.0
    assert usage["messages"] == 0

    print("✓ New session: 126K tokens available")


def test_add_messages_increments_tokens():
    """Test that adding messages increments token count."""
    manager = ContextWindowManager(max_tokens=126000)

    # Add some messages
    manager.add_message("session_1", "user", "Hello, how are you?")
    manager.add_message("session_1", "assistant", "I'm doing well, thanks for asking!")

    usage = manager.get_token_usage("session_1")

    assert usage["total_tokens"] > 0
    assert usage["messages"] == 2
    assert usage["available"] < 126000

    print(f"✓ Added 2 messages: {usage['total_tokens']} tokens used")


def test_auto_compaction_triggers_at_threshold():
    """Test that compaction triggers at 80% threshold."""
    # Small limit for testing
    manager = ContextWindowManager(
        max_tokens=1000,
        compact_threshold=0.80,  # 800 tokens
        keep_recent_messages=3,
    )

    # Add messages until we hit threshold
    compaction_triggered = False

    for i in range(20):
        # Each message ~50 tokens
        triggered = manager.add_message(
            "session_1",
            "user" if i % 2 == 0 else "assistant",
            f"This is message number {i} with some content to make it have tokens." * 3,
        )

        if triggered:
            compaction_triggered = True
            break

    assert compaction_triggered, "Compaction should have triggered"

    usage = manager.get_token_usage("session_1")

    # After compaction, should be under threshold
    assert usage["total_tokens"] < 800, f"Expected <800 tokens, got {usage['total_tokens']}"

    # Should have fewer messages (old ones compressed)
    assert usage["messages"] <= 5, f"Expected <=5 messages after compaction, got {usage['messages']}"

    print(f"✓ Auto-compaction: {usage['total_tokens']} tokens, {usage['messages']} messages")


def test_recent_messages_kept_verbatim():
    """Test that recent messages are kept verbatim during compaction."""
    manager = ContextWindowManager(
        max_tokens=1000,
        compact_threshold=0.50,  # Low threshold to force compaction
        keep_recent_messages=3,
    )

    # Add messages
    recent_contents = []
    for i in range(15):
        content = f"Message {i}: " + ("x" * 50)  # Make it substantial
        manager.add_message(
            "session_1",
            "user" if i % 2 == 0 else "assistant",
            content,
        )

        # Track last 3
        if i >= 12:
            recent_contents.append(content)

    # Get context for LLM
    context = manager.get_context_for_llm("session_1")

    # Last 3 messages should be intact (not in summary)
    # Note: context might have summary + 3 recent = 4 messages
    # Check that recent contents are present
    context_text = " ".join(msg["content"] for msg in context)

    for content in recent_contents:
        assert content in context_text, f"Recent message should be kept verbatim"

    print(f"✓ Recent messages preserved: {len(recent_contents)} messages intact")


def test_reset_session_clears_context():
    """Test that resetting session clears context."""
    manager = ContextWindowManager(max_tokens=126000)

    # Add messages
    manager.add_message("session_1", "user", "Hello")
    manager.add_message("session_1", "assistant", "Hi there!")

    usage_before = manager.get_token_usage("session_1")
    assert usage_before["total_tokens"] > 0

    # Reset
    manager.reset_session("session_1")

    # Should be fresh
    usage_after = manager.get_token_usage("session_1")
    assert usage_after["total_tokens"] == 0
    assert usage_after["messages"] == 0
    assert usage_after["available"] == 126000

    print("✓ Session reset: 126K tokens available again")


def test_multiple_sessions_independent():
    """Test that different sessions are tracked independently."""
    manager = ContextWindowManager(max_tokens=126000)

    manager.add_message("session_1", "user", "Hello from session 1")
    manager.add_message("session_2", "user", "Hello from session 2 with extra text")

    usage_1 = manager.get_token_usage("session_1")
    usage_2 = manager.get_token_usage("session_2")

    # Both should have messages
    assert usage_1["messages"] == 1
    assert usage_2["messages"] == 1

    # Different token counts (session 2 has more text)
    assert usage_1["total_tokens"] < usage_2["total_tokens"]

    print(f"✓ Independent sessions: session_1={usage_1['total_tokens']}, session_2={usage_2['total_tokens']}")


def test_compaction_stats_tracked():
    """Test that compaction stats are tracked."""
    manager = ContextWindowManager(
        max_tokens=1000,
        compact_threshold=0.50,
        keep_recent_messages=2,
    )

    # Add enough messages to trigger multiple compactions
    for i in range(30):
        manager.add_message(
            "session_1",
            "user" if i % 2 == 0 else "assistant",
            f"Message {i} with content" * 10,
        )

    stats = manager.get_stats()
    usage = manager.get_token_usage("session_1")

    assert stats["total_compactions"] > 0
    assert usage["compactions"] > 0
    assert stats["tokens_saved"] > 0

    print(f"✓ Compaction stats: {stats['total_compactions']} compactions, {stats['tokens_saved']} tokens saved")


def test_get_context_for_llm_format():
    """Test that context is properly formatted for LLM."""
    manager = ContextWindowManager(max_tokens=126000)

    manager.add_message("session_1", "user", "What's the weather?")
    manager.add_message("session_1", "assistant", "It's sunny and 72°F")

    context = manager.get_context_for_llm("session_1")

    assert len(context) == 2
    assert context[0]["role"] == "user"
    assert context[0]["content"] == "What's the weather?"
    assert context[1]["role"] == "assistant"
    assert context[1]["content"] == "It's sunny and 72°F"

    print(f"✓ LLM context format: {len(context)} messages with role/content")


if __name__ == "__main__":
    """Run tests manually."""
    import sys

    def run_all_tests():
        print("\n=== ContextWindowManager Test Suite ===\n")

        tests = [
            ("New Session Fresh Context", test_new_session_fresh_context),
            ("Add Messages", test_add_messages_increments_tokens),
            ("Auto-Compaction Trigger", test_auto_compaction_triggers_at_threshold),
            ("Recent Messages Preserved", test_recent_messages_kept_verbatim),
            ("Session Reset", test_reset_session_clears_context),
            ("Independent Sessions", test_multiple_sessions_independent),
            ("Compaction Stats", test_compaction_stats_tracked),
            ("LLM Context Format", test_get_context_for_llm_format),
        ]

        passed = 0
        failed = 0

        for name, test_func in tests:
            try:
                test_func()
                passed += 1
            except Exception as e:
                print(f"✗ {name}: {e}")
                import traceback
                traceback.print_exc()
                failed += 1

        print(f"\n=== Results: {passed} passed, {failed} failed ===\n")

        return failed == 0

    success = run_all_tests()
    sys.exit(0 if success else 1)
