"""
Model Capability Registry for Universal LLM Support

This module provides a capability-based system for working with any LLM model,
automatically detecting features and providing graceful degradation.
"""

from dataclasses import dataclass
from typing import Optional, Tuple, Dict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelCapabilities:
    """Defines capabilities of an LLM model."""

    supports_tool_calling: bool = True
    supports_structured_output: bool = True
    supports_temperature: bool = True
    supports_streaming: bool = True
    max_tokens_param: str = "max_tokens"
    default_temperature: float = 0.3
    temperature_range: Tuple[float, float] = (0.0, 2.0)
    context_window: int = 8192
    fallback_strategy: str = "retry"

    def validate_temperature(self, temperature: Optional[float]) -> float:
        """Validate and normalize temperature value."""
        if not self.supports_temperature:
            return self.default_temperature

        if temperature is None:
            return self.default_temperature

        min_temp, max_temp = self.temperature_range
        return max(min_temp, min(temperature, max_temp))

    def get_max_tokens_param_name(self) -> str:
        """Get the correct parameter name for max tokens."""
        return self.max_tokens_param

    def can_use_tools(self) -> bool:
        """Check if model can use any form of tool calling."""
        return self.supports_tool_calling or self.supports_structured_output


MODEL_REGISTRY: Dict[str, ModelCapabilities] = {
    "gpt-5": ModelCapabilities(
        supports_temperature=False,
        default_temperature=1.0,
        max_tokens_param="max_completion_tokens",
        context_window=128000,
        temperature_range=(1.0, 1.0),
    ),
    "gpt-4": ModelCapabilities(
        supports_tool_calling=True,
        supports_structured_output=True,
        context_window=8192,
        default_temperature=0.3,
    ),
    "gpt-4-turbo": ModelCapabilities(
        supports_tool_calling=True,
        supports_structured_output=True,
        context_window=128000,
        default_temperature=0.3,
    ),
    "gpt-4o": ModelCapabilities(
        supports_tool_calling=True,
        supports_structured_output=True,
        context_window=128000,
        default_temperature=0.3,
    ),
    "gpt-3.5-turbo": ModelCapabilities(
        supports_tool_calling=True,
        context_window=16385,
        default_temperature=0.3,
    ),
    "claude-3.5-sonnet": ModelCapabilities(
        supports_tool_calling=True,
        supports_structured_output=True,
        context_window=200000,
        default_temperature=0.3,
        max_tokens_param="max_tokens",
    ),
    "claude-3-opus": ModelCapabilities(
        supports_tool_calling=True,
        supports_structured_output=True,
        context_window=200000,
        default_temperature=0.3,
    ),
    "claude-3-sonnet": ModelCapabilities(
        supports_tool_calling=True,
        supports_structured_output=True,
        context_window=200000,
        default_temperature=0.3,
    ),
    "claude-3-haiku": ModelCapabilities(
        supports_tool_calling=True,
        supports_structured_output=True,
        context_window=200000,
        default_temperature=0.3,
    ),
    "llama-3.1-70b": ModelCapabilities(
        supports_tool_calling=True,
        supports_structured_output=True,
        context_window=128000,
        default_temperature=0.3,
    ),
    "meta/llama-3.1-70b-instruct": ModelCapabilities(
        supports_tool_calling=True,
        supports_structured_output=True,
        context_window=128000,
        default_temperature=0.3,
    ),
    "llama-3.1-8b": ModelCapabilities(
        supports_tool_calling=True,
        supports_structured_output=True,
        context_window=128000,
        default_temperature=0.3,
    ),
    "mistral-large": ModelCapabilities(
        supports_tool_calling=True,
        supports_structured_output=True,
        context_window=128000,
        default_temperature=0.3,
    ),
    "mistral-medium": ModelCapabilities(
        supports_tool_calling=True,
        supports_structured_output=True,
        context_window=32000,
        default_temperature=0.3,
    ),
    "mixtral-8x7b": ModelCapabilities(
        supports_tool_calling=True,
        supports_structured_output=False,
        context_window=32000,
        default_temperature=0.3,
    ),
    "default": ModelCapabilities(
        supports_tool_calling=True,
        supports_structured_output=False,
        context_window=8192,
        default_temperature=0.3,
    ),
}


class ModelCapabilityDetector:
    """Detects and manages model capabilities."""

    @staticmethod
    def get_capabilities(model_name: str) -> ModelCapabilities:
        """
        Get capabilities for a model, with automatic detection.

        Args:
            model_name: Name of the model

        Returns:
            ModelCapabilities for the model
        """
        if not model_name:
            logger.warning("No model name provided, using default capabilities")
            return MODEL_REGISTRY["default"]

        model_name_lower = model_name.lower()

        if model_name in MODEL_REGISTRY:
            logger.info(f"Found exact match for model: {model_name}")
            return MODEL_REGISTRY[model_name]

        for registered_model, capabilities in MODEL_REGISTRY.items():
            if registered_model in model_name_lower or model_name_lower in registered_model:
                logger.info(f"Found partial match: {registered_model} for model: {model_name}")
                return capabilities

        logger.warning(f"Unknown model: {model_name}, using default capabilities with auto-detection")
        detected = ModelCapabilityDetector._auto_detect(model_name)
        return detected

    @staticmethod
    def _auto_detect(model_name: str) -> ModelCapabilities:
        """
        Auto-detect capabilities based on model name patterns.

        Args:
            model_name: Name of the model

        Returns:
            ModelCapabilities with best-guess settings
        """
        model_lower = model_name.lower()

        if any(x in model_lower for x in ["gpt-4", "gpt4"]):
            logger.info("Detected GPT-4 family model")
            return ModelCapabilities(
                supports_tool_calling=True,
                supports_structured_output=True,
                context_window=128000,
                default_temperature=0.3,
            )

        if any(x in model_lower for x in ["gpt-5", "gpt5"]):
            logger.info("Detected GPT-5 family model")
            return ModelCapabilities(
                supports_temperature=False,
                default_temperature=1.0,
                max_tokens_param="max_completion_tokens",
                context_window=128000,
            )

        if "claude" in model_lower:
            logger.info("Detected Claude family model")
            return ModelCapabilities(
                supports_tool_calling=True,
                supports_structured_output=True,
                context_window=200000,
                default_temperature=0.3,
            )

        if "llama" in model_lower:
            logger.info("Detected Llama family model")
            context_size = 128000 if "3.1" in model_lower or "3.2" in model_lower else 8192
            return ModelCapabilities(
                supports_tool_calling=True,
                supports_structured_output=True,
                context_window=context_size,
                default_temperature=0.3,
            )

        if "mistral" in model_lower or "mixtral" in model_lower:
            logger.info("Detected Mistral/Mixtral family model")
            return ModelCapabilities(
                supports_tool_calling=True,
                supports_structured_output=True,
                context_window=32000,
                default_temperature=0.3,
            )

        logger.warning(f"Could not auto-detect model type for: {model_name}, using conservative defaults")
        return MODEL_REGISTRY["default"]

    @staticmethod
    def register_model(model_name: str, capabilities: ModelCapabilities):
        """
        Register a new model with specific capabilities.

        Args:
            model_name: Name of the model
            capabilities: ModelCapabilities for the model
        """
        MODEL_REGISTRY[model_name] = capabilities
        logger.info(f"Registered new model: {model_name}")
