"""
LLM Response Cache

Caches LLM completions to reduce costs and latency.

Configuration:
- TTL: 24 hours (86400s) for general queries
- TTL: 4 hours (14400s) for time-sensitive queries
- Stale-while-revalidate: 1 hour (3600s)

Expected Impact:
- Repeated queries: 5s -> 0.05s (100x faster)
- Cost savings: ~70% reduction in LLM calls
"""

import logging
import re
from typing import Any, Dict, List, Optional

from orchestrator.caching.base_cache import BaseCache, CacheConfig

logger = logging.getLogger(__name__)


class LLMCache(BaseCache):
    """
    Cache for LLM responses.

    Automatically detects time-sensitive queries and uses shorter TTL.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize LLM cache with aggressive TTL."""
        config = CacheConfig(
            ttl_seconds=86400,  # 24 hours default
            stale_while_revalidate_seconds=3600,  # 1 hour grace
            key_prefix="llm",
        )
        super().__init__(config, redis_url)

        # Time-sensitive patterns
        self.time_sensitive_patterns = [
            r"\btoday\b",
            r"\bnow\b",
            r"\bcurrent\b",
            r"\bthis (morning|afternoon|evening|week|month)\b",
            r"\btomorrow\b",
            r"\byesterday\b",
        ]

    def _is_time_sensitive(self, prompt: str) -> bool:
        """Check if prompt contains time-sensitive keywords."""
        prompt_lower = prompt.lower()
        return any(re.search(pattern, prompt_lower) for pattern in self.time_sensitive_patterns)

    async def get_cached_completion(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> Optional[str]:
        """
        Get cached LLM completion.

        Args:
            prompt: The prompt
            model: Model name
            temperature: Temperature setting
            **kwargs: Additional model parameters

        Returns:
            Cached response or None
        """
        cache_key = self._make_cache_key(prompt, model, temperature, **kwargs)
        return await self.get(cache_key)

    async def cache_completion(
        self,
        prompt: str,
        response: str,
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> bool:
        """
        Cache LLM completion.

        Args:
            prompt: The prompt
            response: The LLM response
            model: Model name
            temperature: Temperature setting
            **kwargs: Additional model parameters

        Returns:
            True if cached successfully
        """
        cache_key = self._make_cache_key(prompt, model, temperature, **kwargs)

        # Use shorter TTL for time-sensitive queries
        ttl = 14400 if self._is_time_sensitive(prompt) else self.config.ttl_seconds

        return await self.set(cache_key, response, ttl)

    def _make_cache_key(
        self,
        prompt: str,
        model: str,
        temperature: float,
        **kwargs,
    ) -> str:
        """Create cache key for LLM completion."""
        # Include important parameters in key
        key_parts = [
            prompt,
            model,
            f"temp={temperature}",
        ]

        # Add other relevant kwargs
        for key in ["max_tokens", "top_p", "frequency_penalty", "presence_penalty"]:
            if key in kwargs:
                key_parts.append(f"{key}={kwargs[key]}")

        return self.compute_key(*key_parts)

    async def get_or_generate(
        self,
        prompt: str,
        model: str,
        generate_fn,
        temperature: float = 0.7,
        **kwargs,
    ) -> str:
        """
        Get cached response or generate new one.

        Args:
            prompt: The prompt
            model: Model name
            generate_fn: Async function that generates response
            temperature: Temperature setting
            **kwargs: Additional model parameters

        Returns:
            LLM response (cached or generated)
        """
        cache_key = self._make_cache_key(prompt, model, temperature, **kwargs)

        # For temperature > 0.5, always generate (high randomness)
        if temperature > 0.5:
            response = await generate_fn()
            # Still cache for similar queries with same temp
            await self.cache_completion(prompt, response, model, temperature, **kwargs)
            return response

        # Use cache with stale-while-revalidate
        ttl = 14400 if self._is_time_sensitive(prompt) else self.config.ttl_seconds
        return await self.get_or_compute(cache_key, generate_fn, ttl)
