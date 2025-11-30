"""
Plan Cache

Caches execution plans from the SmartPlanner.

Configuration:
- TTL: 30 days (2592000s) - plans rarely change
- Stale-while-revalidate: 7 days (604800s)

This is primarily for L3 (LLM-generated) plans that are expensive to create.
L1 (pattern) and L2 (semantic) caches are in-memory and don't need Redis.

Expected Impact:
- Repeated novel queries: 4s → 0.1s (40x faster)
"""

import logging
from typing import Any, Dict, Optional

from orchestrator.caching.base_cache import BaseCache, CacheConfig
from orchestrator.agents.query_analyzer import ToolPlan

logger = logging.getLogger(__name__)


class PlanCache(BaseCache):
    """
    Cache for execution plans.

    Plans are long-lived since query patterns don't change often.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize plan cache with long TTL."""
        config = CacheConfig(
            ttl_seconds=2592000,  # 30 days
            stale_while_revalidate_seconds=604800,  # 7 days grace
            key_prefix="plan",
        )
        super().__init__(config, redis_url)

    async def get_cached_plan(self, query: str, context: Optional[Dict] = None) -> Optional[ToolPlan]:
        """
        Get cached plan for query.

        Args:
            query: User query
            context: Optional context

        Returns:
            Cached ToolPlan or None
        """
        cache_key = self._make_cache_key(query, context)
        cached = await self.get(cache_key)

        if cached:
            try:
                # Reconstruct ToolPlan from cached dict
                return ToolPlan(**cached)
            except Exception as e:
                logger.error(f"Failed to deserialize cached plan: {e}")
                return None

        return None

    async def cache_plan(
        self,
        query: str,
        plan: ToolPlan,
        context: Optional[Dict] = None,
    ) -> bool:
        """
        Cache execution plan.

        Args:
            query: User query
            plan: ToolPlan to cache
            context: Optional context

        Returns:
            True if cached successfully
        """
        cache_key = self._make_cache_key(query, context)

        # Convert ToolPlan to dict for JSON serialization
        plan_dict = plan.model_dump() if hasattr(plan, "model_dump") else plan.dict()

        return await self.set(cache_key, plan_dict)

    def _make_cache_key(self, query: str, context: Optional[Dict]) -> str:
        """Create cache key for plan."""
        # Context is optional - most queries don't need it for caching
        if context:
            return self.compute_key(query, str(context))
        return self.compute_key(query)

    async def get_or_plan(
        self,
        query: str,
        plan_fn,
        context: Optional[Dict] = None,
    ) -> ToolPlan:
        """
        Get cached plan or generate new one.

        Args:
            query: User query
            plan_fn: Async function that generates plan
            context: Optional context

        Returns:
            ToolPlan (cached or generated)
        """
        cache_key = self._make_cache_key(query, context)

        async def compute():
            plan = await plan_fn()
            # Convert to dict for caching
            return plan.model_dump() if hasattr(plan, "model_dump") else plan.dict()

        cached = await self.get_or_compute(cache_key, compute)

        # Convert back to ToolPlan
        try:
            return ToolPlan(**cached)
        except Exception as e:
            logger.error(f"Failed to deserialize plan: {e}")
            # Fallback to generating new plan
            return await plan_fn()
