"""
LLM Client using LangChain for unified interface to NVIDIA NIM and OpenAI.
"""

import os
from typing import Optional

from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_openai import ChatOpenAI


class LLMClient:
    """Unified LLM client using LangChain, supporting multiple providers."""

    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize LLM client with LangChain.

        Args:
            provider: 'nvidia' or 'openai'. Defaults to env var AI_PROVIDER or 'openai'
            model: specific model name to override default
        """
        self.provider = provider or os.getenv("AI_PROVIDER", "openai")

        if self.provider == "nvidia":
            api_key = os.getenv("NVIDIA_API_KEY")
            if not api_key:
                raise ValueError("NVIDIA_API_KEY not found")
            self.llm = ChatNVIDIA(
                model=model or "meta/llama3-70b-instruct",
                nvidia_api_key=api_key,
            )
        elif self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found")
            # Allow override, else env var, else default
            model_name = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            self.llm = ChatOpenAI(
                model=model_name,
                openai_api_key=api_key,
                temperature=0.3,
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def call(self, prompt: str, temperature: float = 0.3, max_tokens: int = 1024) -> str:
        """
        Call the LLM with a prompt using LangChain.

        Args:
            prompt: The prompt to send
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            The LLM response as a string
        """
        # Update temperature if different from default
        if temperature != 0.3 and hasattr(self.llm, "temperature"):
            self.llm.temperature = temperature

        response = self.llm.invoke(prompt)
        return response.content

    def call_json(self, prompt: str, temperature: float = 0.2, max_tokens: int = 1024) -> dict:
        """
        Call the LLM and parse JSON response using LangChain.

        Args:
            prompt: The prompt to send (should request JSON output)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Parsed JSON response as dict
        """
        import json

        # Add JSON formatting instruction to prompt
        json_prompt = f"{prompt}\n\nRespond with valid JSON only, no markdown code blocks."
        response_text = self.call(json_prompt, temperature, max_tokens)

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
        return f"LLMClient(provider={self.provider}, llm={type(self.llm).__name__})"
