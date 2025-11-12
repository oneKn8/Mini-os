"""
LLM Client - Unified interface for NVIDIA NIM and OpenAI
"""

import json
import os
from typing import Optional

import requests


class LLMClient:
    """Unified LLM client supporting multiple providers."""

    def __init__(self, provider: Optional[str] = None):
        """
        Initialize LLM client.

        Args:
            provider: 'nvidia' or 'openai'. Defaults to env var AI_PROVIDER or 'openai'
        """
        self.provider = provider or os.getenv("AI_PROVIDER", "openai")

        if self.provider == "nvidia":
            self.api_key = os.getenv("NVIDIA_API_KEY")
            self.model = "meta/llama3-70b-instruct"
            self.api_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        elif self.provider == "openai":
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            self.api_url = "https://api.openai.com/v1/chat/completions"
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

        if not self.api_key:
            raise ValueError(f"API key not found for provider: {self.provider}")

    def call(self, prompt: str, temperature: float = 0.3, max_tokens: int = 1024) -> str:
        """
        Call the LLM with a prompt.

        Args:
            prompt: The prompt to send
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            The LLM response as a string
        """
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    def call_json(self, prompt: str, temperature: float = 0.2, max_tokens: int = 1024) -> dict:
        """
        Call the LLM and parse JSON response.

        Args:
            prompt: The prompt to send (should request JSON output)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Parsed JSON response as dict
        """
        response_text = self.call(prompt, temperature, max_tokens)

        # Try to extract JSON if wrapped in markdown code blocks
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()

        return json.loads(response_text)

    def __repr__(self):
        return f"LLMClient(provider={self.provider}, model={self.model})"
