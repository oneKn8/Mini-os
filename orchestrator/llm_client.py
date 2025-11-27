"""
LLM Client using LangChain for unified interface to NVIDIA NIM and OpenAI.

Enhanced with:
- Tool binding (bind_tools)
- Structured output (with_structured_output)
- Conversation history management
- Async support
- Streaming support
- Universal model support via capability registry
"""

import json
import logging
import os
from typing import AsyncIterator, Dict, List, Optional, Type

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from orchestrator.llm_capabilities import ModelCapabilityDetector, ModelCapabilities

logger = logging.getLogger(__name__)

# Try to import providers
try:
    from langchain_nvidia_ai_endpoints import ChatNVIDIA

    NVIDIA_AVAILABLE = True
except ImportError:
    ChatNVIDIA = None
    NVIDIA_AVAILABLE = False
    logger.debug("NVIDIA AI Endpoints not available")

try:
    from langchain_openai import ChatOpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    ChatOpenAI = None
    OPENAI_AVAILABLE = False
    logger.debug("OpenAI not available")


class LLMClient:
    """
    Unified LLM client using LangChain, supporting multiple providers.

    Features:
    - Multiple providers (OpenAI, NVIDIA NIM)
    - Tool binding for function calling
    - Structured output for reliable JSON
    - Conversation history management
    - Async and streaming support
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ):
        """
        Initialize LLM client with LangChain.

        Args:
            provider: 'nvidia' or 'openai'. Defaults to env var AI_PROVIDER or 'openai'
            model: specific model name to override default
            temperature: Default sampling temperature
            max_tokens: Default max tokens to generate
        """
        self.provider = provider or os.getenv("AI_PROVIDER", "openai")
        self.default_temperature = temperature
        self.default_max_tokens = max_tokens
        self._tools: List[BaseTool] = []
        self._conversation_history: List[BaseMessage] = []
        self._model_name: Optional[str] = model or os.getenv(
            "OPENAI_MODEL" if self.provider == "openai" else "NVIDIA_MODEL", None
        )

        self.capabilities: ModelCapabilities = ModelCapabilityDetector.get_capabilities(self._model_name or "")

        self.llm = self._create_llm(model)

    def _create_llm(self, model: Optional[str] = None) -> BaseChatModel:
        """Create the underlying LLM instance using capability-based configuration."""
        if self.provider == "nvidia":
            if not NVIDIA_AVAILABLE:
                raise RuntimeError("langchain-nvidia-ai-endpoints is required for NVIDIA provider")
            api_key = os.getenv("NVIDIA_API_KEY")
            if not api_key:
                raise ValueError("NVIDIA_API_KEY not found")

            model_name = model or os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct")
            self._model_name = model_name
            self.capabilities = ModelCapabilityDetector.get_capabilities(model_name)

            temperature = self.capabilities.validate_temperature(self.default_temperature)

            return ChatNVIDIA(
                model=model_name,
                nvidia_api_key=api_key,
                temperature=temperature,
                max_tokens=self.default_max_tokens,
            )

        elif self.provider == "openai":
            if not OPENAI_AVAILABLE:
                raise RuntimeError("langchain-openai is required for OpenAI provider")
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found")

            model_name = model or os.getenv("OPENAI_MODEL", "gpt-5")
            self._model_name = model_name
            self.capabilities = ModelCapabilityDetector.get_capabilities(model_name)

            temperature = self.capabilities.validate_temperature(self.default_temperature)
            max_tokens_param = self.capabilities.get_max_tokens_param_name()

            if max_tokens_param == "max_completion_tokens":
                return ChatOpenAI(
                    model=model_name,
                    openai_api_key=api_key,
                    temperature=temperature,
                    model_kwargs={"max_completion_tokens": self.default_max_tokens},
                )
            else:
                return ChatOpenAI(
                    model=model_name,
                    openai_api_key=api_key,
                    temperature=temperature,
                    max_tokens=self.default_max_tokens,
                )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    # =========================================================================
    # Tool Binding
    # =========================================================================

    def bind_tools(self, tools: List[BaseTool], tool_choice: Optional[str] = None) -> "LLMClient":
        """
        Bind tools to the LLM for function calling.

        Args:
            tools: List of LangChain tools to bind
            tool_choice: Optional tool choice strategy ('auto', 'any', or specific tool name)

        Returns:
            Self for chaining
        """
        self._tools = tools
        kwargs = {}
        if tool_choice:
            kwargs["tool_choice"] = tool_choice
        self.llm = self.llm.bind_tools(tools, **kwargs)
        return self

    def get_bound_tools(self) -> List[BaseTool]:
        """Get the currently bound tools."""
        return self._tools

    # =========================================================================
    # Structured Output
    # =========================================================================

    def with_structured_output(
        self, schema: Type[BaseModel], method: str = "function_calling", include_raw: bool = False
    ) -> BaseChatModel:
        """
        Create an LLM that outputs structured data matching a Pydantic schema.

        Uses LMFE (Logit-based Model Format Enforcement) when available.

        Args:
            schema: Pydantic model defining the output structure
            method: Method to use ('function_calling' or 'json_mode')
            include_raw: Whether to include raw LLM output alongside parsed

        Returns:
            A runnable that outputs structured data
        """
        return self.llm.with_structured_output(schema, method=method, include_raw=include_raw)

    # =========================================================================
    # Conversation History Management
    # =========================================================================

    def add_system_message(self, content: str) -> None:
        """Add a system message to conversation history."""
        self._conversation_history.append(SystemMessage(content=content))

    def add_user_message(self, content: str) -> None:
        """Add a user message to conversation history."""
        self._conversation_history.append(HumanMessage(content=content))

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to conversation history."""
        self._conversation_history.append(AIMessage(content=content))

    def set_conversation_history(self, messages: List[Dict[str, str]]) -> None:
        """
        Set conversation history from a list of message dicts.

        Args:
            messages: List of {"role": "user"|"assistant"|"system", "content": "..."}
        """
        self._conversation_history = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                self._conversation_history.append(SystemMessage(content=content))
            elif role == "user":
                self._conversation_history.append(HumanMessage(content=content))
            elif role == "assistant":
                self._conversation_history.append(AIMessage(content=content))

    def get_conversation_history(self) -> List[BaseMessage]:
        """Get the current conversation history."""
        return self._conversation_history.copy()

    def clear_conversation_history(self) -> None:
        """Clear conversation history."""
        self._conversation_history = []

    # =========================================================================
    # Chat Methods (with history)
    # =========================================================================

    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        use_history: bool = True,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Send a chat message with optional conversation history.

        Args:
            message: The user message
            system_prompt: Optional system prompt to prepend
            use_history: Whether to include conversation history
            temperature: Override default temperature

        Returns:
            The assistant's response
        """
        messages = self._build_messages(message, system_prompt, use_history)

        if temperature and temperature != self.default_temperature:
            validated_temp = self.capabilities.validate_temperature(temperature)

            if validated_temp != self.default_temperature and self.capabilities.supports_temperature:
                llm = self.llm.bind(temperature=validated_temp) if hasattr(self.llm, "bind") else self.llm
            else:
                llm = self.llm
        else:
            llm = self.llm

        response = llm.invoke(messages)
        response_content = response.content if hasattr(response, "content") else str(response)

        # Update history
        if use_history:
            self._conversation_history.append(HumanMessage(content=message))
            self._conversation_history.append(AIMessage(content=response_content))

        return response_content

    async def achat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        use_history: bool = True,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Async version of chat.

        Args:
            message: The user message
            system_prompt: Optional system prompt to prepend
            use_history: Whether to include conversation history
            temperature: Override default temperature

        Returns:
            The assistant's response
        """
        messages = self._build_messages(message, system_prompt, use_history)

        response = await self.llm.ainvoke(messages)
        response_content = response.content if hasattr(response, "content") else str(response)

        # Update history
        if use_history:
            self._conversation_history.append(HumanMessage(content=message))
            self._conversation_history.append(AIMessage(content=response_content))

        return response_content

    async def astream_chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        use_history: bool = True,
    ) -> AsyncIterator[str]:
        """
        Stream chat response asynchronously.

        Args:
            message: The user message
            system_prompt: Optional system prompt to prepend
            use_history: Whether to include conversation history

        Yields:
            Chunks of the response as they're generated
        """
        messages = self._build_messages(message, system_prompt, use_history)

        full_response = ""
        async for chunk in self.llm.astream(messages):
            chunk_content = chunk.content if hasattr(chunk, "content") else str(chunk)
            full_response += chunk_content
            yield chunk_content

        # Update history after stream completes
        if use_history:
            self._conversation_history.append(HumanMessage(content=message))
            self._conversation_history.append(AIMessage(content=full_response))

    def _build_messages(self, message: str, system_prompt: Optional[str], use_history: bool) -> List[BaseMessage]:
        """Build the messages list for a chat call."""
        messages = []

        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))

        if use_history:
            messages.extend(self._conversation_history)

        messages.append(HumanMessage(content=message))
        return messages

    # =========================================================================
    # Invoke with Messages (raw message list)
    # =========================================================================

    def invoke_messages(self, messages: List[BaseMessage]) -> AIMessage:
        """
        Invoke the LLM with a raw message list.

        Args:
            messages: List of LangChain messages

        Returns:
            The AI response message
        """
        return self.llm.invoke(messages)

    async def ainvoke_messages(self, messages: List[BaseMessage]) -> AIMessage:
        """
        Async invoke the LLM with a raw message list.

        Args:
            messages: List of LangChain messages

        Returns:
            The AI response message
        """
        return await self.llm.ainvoke(messages)

    # =========================================================================
    # Legacy Methods (backward compatibility)
    # =========================================================================

    def call(self, prompt: str, temperature: float = 0.3, max_tokens: int = 1024) -> str:
        """
        Call the LLM with a simple prompt (legacy method).

        Args:
            prompt: The prompt to send
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            The LLM response as a string
        """
        response = self.llm.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)

    def call_json(self, prompt: str, temperature: float = 0.2, max_tokens: int = 1024) -> dict:
        """
        Call the LLM and parse JSON response (legacy method).

        Args:
            prompt: The prompt to send (should request JSON output)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Parsed JSON response as dict
        """
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

    # =========================================================================
    # Utility
    # =========================================================================

    def get_model_name(self) -> str:
        """Get the current model name."""
        if hasattr(self.llm, "model_name"):
            return self.llm.model_name
        elif hasattr(self.llm, "model"):
            return self.llm.model
        return "unknown"

    def get_underlying_llm(self) -> BaseChatModel:
        """Get the underlying LangChain LLM instance."""
        return self.llm

    def get_capabilities(self) -> ModelCapabilities:
        """Get the model capabilities."""
        return self.capabilities

    def __repr__(self):
        return f"LLMClient(provider={self.provider}, model={self.get_model_name()}, tools={len(self._tools)})"


# =========================================================================
# Convenience Functions
# =========================================================================


def get_default_llm() -> LLMClient:
    """Get a default LLM client based on environment configuration."""
    return LLMClient()


def create_llm_with_tools(tools: List[BaseTool], provider: Optional[str] = None) -> LLMClient:
    """Create an LLM client with tools pre-bound."""
    client = LLMClient(provider=provider)
    client.bind_tools(tools)
    return client
