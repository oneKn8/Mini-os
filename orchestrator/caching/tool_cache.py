"""
Tool Result Cache

Caches tool execution results.

Configuration per tool type:
- Email: 2 hours (7200s) + webhook invalidation
- Calendar: 4 hours (14400s) + webhook invalidation
- Weather: 30 minutes (1800s)
- Search: 1 hour (3600s)

Expected Impact:
- Repeated tool calls: 5s → 0.1s (50x faster)
- Reduced API calls to external services
"""

import logging
from typing import Any, Dict, Optional

from orchestrator.caching.base_cache import BaseCache, CacheConfig

logger = logging.getLogger(__name__)


# Tool-specific TTL configurations (in seconds)
TOOL_TTL_CONFIG = {
    # Email tools
    "search_emails": 7200,  # 2 hours
    "get_email": 7200,
    "get_inbox_items": 7200,

    # Calendar tools
    "get_todays_events": 14400,  # 4 hours
    "get_upcoming_events": 14400,
    "get_event": 14400,

    # Weather tools
    "get_current_weather": 1800,  # 30 minutes
    "get_weather_forecast": 3600,  # 1 hour

    # Priority/planning tools
    "get_priority_items": 7200,  # 2 hours
    "plan_day": 14400,  # 4 hours

    # Default for unknown tools
    "default": 3600,  # 1 hour
}


class ToolCache(BaseCache):
    """
    Cache for tool execution results.

    Automatically selects TTL based on tool type.
    Supports webhook invalidation for email/calendar updates.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize tool cache."""
        config = CacheConfig(
            ttl_seconds=3600,  # Default 1 hour
            stale_while_revalidate_seconds=300,  # 5 minute grace
            key_prefix="tool",
        )
        super().__init__(config, redis_url)

    def _get_tool_ttl(self, tool_name: str) -> int:
        """Get TTL for specific tool."""
        return TOOL_TTL_CONFIG.get(tool_name, TOOL_TTL_CONFIG["default"])

    async def get_cached_result(
        self,
        tool_name: str,
        args: Dict[str, Any],
    ) -> Optional[Any]:
        """
        Get cached tool result.

        Args:
            tool_name: Name of the tool
            args: Tool arguments

        Returns:
            Cached result or None
        """
        cache_key = self._make_cache_key(tool_name, args)
        return await self.get(cache_key)

    async def cache_result(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any,
    ) -> bool:
        """
        Cache tool result.

        Args:
            tool_name: Name of the tool
            args: Tool arguments
            result: Tool result

        Returns:
            True if cached successfully
        """
        cache_key = self._make_cache_key(tool_name, args)
        ttl = self._get_tool_ttl(tool_name)
        return await self.set(cache_key, result, ttl)

    def _make_cache_key(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Create cache key for tool result."""
        # Sort args for consistent keys
        sorted_args = sorted(args.items()) if args else []
        return self.compute_key(tool_name, *[f"{k}={v}" for k, v in sorted_args])

    async def invalidate_tool_type(self, tool_type: str) -> int:
        """
        Invalidate all cached results for a tool type.

        Useful for webhook invalidation (e.g., new email received).

        Args:
            tool_type: Type prefix (e.g., "search_emails", "get_todays_events")

        Returns:
            Number of keys invalidated
        """
        try:
            redis = self._get_redis()

            if isinstance(redis, dict):
                # In-memory fallback
                prefix = f"{self.config.key_prefix}:{tool_type}"
                keys_to_delete = [k for k in redis.keys() if k.startswith(prefix)]
                for key in keys_to_delete:
                    del redis[key]
                count = len(keys_to_delete)
            else:
                # Redis pattern matching
                pattern = f"{self.config.key_prefix}:*{tool_type}*"
                cursor = 0
                count = 0
                while True:
                    cursor, keys = await redis.scan(cursor, match=pattern, count=100)
                    if keys:
                        await redis.delete(*keys)
                        count += len(keys)
                    if cursor == 0:
                        break

            self._stats["invalidations"] += count
            logger.info(f"Invalidated {count} cache entries for tool type: {tool_type}")
            return count

        except Exception as e:
            logger.error(f"Failed to invalidate tool type {tool_type}: {e}")
            return 0

    async def get_or_execute(
        self,
        tool_name: str,
        args: Dict[str, Any],
        execute_fn,
    ) -> Any:
        """
        Get cached result or execute tool.

        Args:
            tool_name: Name of the tool
            args: Tool arguments
            execute_fn: Async function that executes the tool

        Returns:
            Tool result (cached or executed)
        """
        cache_key = self._make_cache_key(tool_name, args)
        ttl = self._get_tool_ttl(tool_name)

        return await self.get_or_compute(cache_key, execute_fn, ttl)
