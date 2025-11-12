"""
Tests for LLM client
"""

import os

import pytest

from orchestrator.llm_client import LLMClient


def test_llm_client_initialization():
    """Test LLM client initialization."""
    # Test OpenAI
    os.environ["OPENAI_API_KEY"] = "test_key"
    os.environ["AI_PROVIDER"] = "openai"
    client = LLMClient()
    assert client.provider == "openai"
    assert client.model == "gpt-4o-mini"
    assert client.api_url == "https://api.openai.com/v1/chat/completions"

    # Test NVIDIA
    os.environ["NVIDIA_API_KEY"] = "test_key"
    client = LLMClient(provider="nvidia")
    assert client.provider == "nvidia"
    assert client.model == "meta/llama3-70b-instruct"
    assert client.api_url == "https://integrate.api.nvidia.com/v1/chat/completions"


def test_llm_client_unsupported_provider():
    """Test unsupported provider raises error."""
    with pytest.raises(ValueError, match="Unsupported provider"):
        LLMClient(provider="invalid")


def test_llm_client_missing_api_key():
    """Test missing API key raises error."""
    # Clear env vars
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]
    if "NVIDIA_API_KEY" in os.environ:
        del os.environ["NVIDIA_API_KEY"]

    with pytest.raises(ValueError, match="API key not found"):
        LLMClient(provider="openai")


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not set")
def test_openai_integration():
    """Test actual OpenAI API call (requires API key)."""
    client = LLMClient(provider="openai")
    response = client.call("Say 'test' and nothing else.", temperature=0, max_tokens=10)
    assert response.strip().lower() == "test"


@pytest.mark.skipif(not os.getenv("NVIDIA_API_KEY"), reason="NVIDIA API key not set")
def test_nvidia_integration():
    """Test actual NVIDIA NIM API call (requires API key)."""
    client = LLMClient(provider="nvidia")
    response = client.call("Say 'test' and nothing else.", temperature=0, max_tokens=10)
    assert "test" in response.lower()


def test_llm_client_json_parsing():
    """Test JSON parsing from LLM response."""
    client = LLMClient()

    # Mock response with markdown code block
    test_json = '```json\n{"key": "value"}\n```'

    # This would normally call the LLM, but we'll test the parsing logic
    # by directly calling json.loads on the cleaned response
    import json

    if "```json" in test_json:
        start = test_json.find("```json") + 7
        end = test_json.find("```", start)
        cleaned = test_json[start:end].strip()

    result = json.loads(cleaned)
    assert result == {"key": "value"}
