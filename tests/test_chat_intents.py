"""
Tests for the chat intent detector.
"""

from backend.api.routes.chat import ChatIntentDetector


def test_detect_plan_day_intent():
    detector = ChatIntentDetector()
    match = detector.detect("Hey, can you plan my day for me?")

    assert match.intent == "plan_day"
    assert match.confidence > 0.5


def test_detect_pending_actions_intent():
    detector = ChatIntentDetector()
    match = detector.detect("Show me the pending actions I need to approve.")

    assert match.intent == "pending_actions"
    assert match.confidence > 0.5


def test_detect_general_intent_when_no_keywords():
    detector = ChatIntentDetector()
    match = detector.detect("Hello there")

    assert match.intent == "general"
    assert match.confidence <= 0.5
