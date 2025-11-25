#!/usr/bin/env python3
"""
Quick test script to verify OpenAI API integration.
"""
import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # noqa: E402

from orchestrator.llm_client import LLMClient  # noqa: E402


def test_openai():
    """Test OpenAI API connection."""
    print("=" * 60)
    print("Testing OpenAI API Integration")
    print("=" * 60)
    print()

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[FAIL] OPENAI_API_KEY not set!")
        print("       Set it in .env file or export OPENAI_API_KEY=your-key")
        return False

    print(f"[OK] API Key found: {api_key[:10]}...{api_key[-4:]}")
    print()

    # Initialize client
    try:
        client = LLMClient(provider="openai")
        print(f"[OK] LLM Client initialized: {client}")
        print()
    except Exception as e:
        print(f"[FAIL] Failed to initialize client: {e}")
        return False

    # Test simple call
    print("Testing simple prompt...")
    try:
        response = client.call("Say 'Hello from OpenAI!' and nothing else.", temperature=0, max_tokens=20)
        print(f"[OK] Response: {response}")
        print()
    except Exception as e:
        print(f"[FAIL] API call failed: {e}")
        return False

    # Test JSON parsing
    print("Testing JSON response...")
    try:
        prompt = """
Return this exact JSON and nothing else:
{
  "status": "success",
  "message": "OpenAI integration working!",
  "agent": "triage"
}
"""
        result = client.call_json(prompt, temperature=0, max_tokens=100)
        print(f"[OK] Parsed JSON: {result}")
        print()
    except Exception as e:
        print(f"[FAIL] JSON parsing failed: {e}")
        return False

    # Test email classification (like triage agent)
    print("Testing email classification...")
    try:
        email_prompt = """
Classify this email and respond with JSON:

From: boss@company.com
Subject: Urgent: Q4 Report Due Tomorrow
Body: Hi, I need the Q4 financial report by tomorrow 5pm. This is critical for board meeting.

Respond with JSON:
{
  "category": "deadline",
  "importance": "critical",
  "action_type": "complete_task",
  "confidence": 0.95
}
"""
        result = client.call_json(email_prompt, temperature=0.2, max_tokens=200)
        print("[OK] Classification result:")
        for key, value in result.items():
            print(f"     {key}: {value}")
        print()
    except Exception as e:
        print(f"[FAIL] Email classification failed: {e}")
        return False

    print("=" * 60)
    print("[SUCCESS] ALL TESTS PASSED!")
    print("=" * 60)
    print()
    print("Your OpenAI API is working correctly!")
    print("The Personal Ops Center is ready to use.")
    return True


def test_nvidia():
    """Test NVIDIA NIM API connection."""
    print("=" * 60)
    print("Testing NVIDIA NIM API Integration")
    print("=" * 60)
    print()

    # Check API key
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        print("[FAIL] NVIDIA_API_KEY not set!")
        print("       Skipping NVIDIA test...")
        return False

    print(f"[OK] API Key found: {api_key[:10]}...{api_key[-4:]}")
    print()

    # Initialize client
    try:
        client = LLMClient(provider="nvidia")
        print(f"[OK] LLM Client initialized: {client}")
        print()
    except Exception as e:
        print(f"[FAIL] Failed to initialize client: {e}")
        return False

    # Test simple call
    print("Testing simple prompt...")
    try:
        response = client.call("Say 'Hello from NVIDIA!' and nothing else.", temperature=0, max_tokens=20)
        print(f"[OK] Response: {response}")
        print()
    except Exception as e:
        print(f"[FAIL] API call failed: {e}")
        return False

    print("[OK] NVIDIA NIM test passed!")
    return True


if __name__ == "__main__":
    # Load .env file
    try:
        from dotenv import load_dotenv

        load_dotenv()
        print("[OK] Loaded .env file")
        print()
    except ImportError:
        print("[WARN] python-dotenv not installed, using system env vars")
        print()

    # Test based on AI_PROVIDER
    provider = os.getenv("AI_PROVIDER", "openai")

    if provider == "openai":
        success = test_openai()
    elif provider == "nvidia":
        success = test_nvidia()
    else:
        print(f"Unknown provider: {provider}")
        success = False

    # Exit with appropriate code
    sys.exit(0 if success else 1)
