"""
Base caching infrastructure with Redis backend.

Provides:
- TTL-based expiration
- Stale-while-revalidate pattern
- Webhook invalidation support
- Cache statistics
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Cache configuration."""

    ttl_seconds: int
    stale_while_revalidate_seconds: int = 0
    max_size_mb: int = 100
    key_prefix: str = "cache"


class BaseCache:
    """
    Base cache with Redis backend and stale-while-revalidate.

    Supports:
    - TTL-based expiration
    - Stale-while-revalidate (serve stale, update in background)
    - Webhook invalidation
    - Statistics
    """

    def __init__(self, config: CacheConfig, redis_url: str = "redis://localhost:6379"):
        """
        Initialize cache.

        Args:
            config: Cache configuration
            redis_url: Redis connection URL
        """
        self.config = config
        self.redis_url = redis_url
        self._redis_client = None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0,
            "errors": 0,
        }

    def _get_redis(self):
        """Lazy load Redis client."""
        if self._redis_client is None:
            try:
                import redis.asyncio as redis

                self._redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                )
                logger.info(f"Connected to Redis: {self.redis_url}")
            except ImportError:
                logger.warning("redis package not installed, using in-memory cache fallback")
                self._redis_client = {}  # Fallback to dict
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}, using in-memory fallback")
                self._redis_client = {}  # Fallback to dict

        return self._redis_client

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        full_key = f"{self.config.key_prefix}:{key}"

        try:
            redis = self._get_redis()

            # In-memory fallback
            if isinstance(redis, dict):
                entry = redis.get(full_key)
                if entry and entry["expires_at"] > time.time():
                    self._stats["hits"] += 1
                    return entry["value"]
                self._stats["misses"] += 1
                return None

            # Redis path
            value_json = await redis.get(full_key)
            if value_json:
                entry = json.loads(value_json)
                self._stats["hits"] += 1
                return entry.get("value")

            self._stats["misses"] += 1
            return None

        except Exception as e:
            logger.error(f"Cache get error for {full_key}: {e}")
            self._stats["errors"] += 1
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Optional custom TTL (uses config default if None)

        Returns:
            True if successful
        """
        full_key = f"{self.config.key_prefix}:{key}"
        ttl = ttl_seconds or self.config.ttl_seconds

        try:
            redis = self._get_redis()

            entry = {
                "value": value,
                "cached_at": time.time(),
                "expires_at": time.time() + ttl,
            }

            # In-memory fallback
            if isinstance(redis, dict):
                redis[full_key] = entry
                return True

            # Redis path
            value_json = json.dumps(entry)
            await redis.setex(full_key, ttl, value_json)
            return True

        except Exception as e:
            logger.error(f"Cache set error for {full_key}: {e}")
            self._stats["errors"] += 1
            return False

    async def invalidate(self, key: str) -> bool:
        """
        Invalidate cache entry.

        Args:
            key: Cache key

        Returns:
            True if successful
        """
        full_key = f"{self.config.key_prefix}:{key}"

        try:
            redis = self._get_redis()

            # In-memory fallback
            if isinstance(redis, dict):
                if full_key in redis:
                    del redis[full_key]
                self._stats["invalidations"] += 1
                return True

            # Redis path
            await redis.delete(full_key)
            self._stats["invalidations"] += 1
            return True

        except Exception as e:
            logger.error(f"Cache invalidation error for {full_key}: {e}")
            self._stats["errors"] += 1
            return False

    async def get_or_compute(
        self,
        key: str,
        compute_fn: Callable,
        ttl_seconds: Optional[int] = None,
    ) -> Any:
        """
        Get from cache or compute and store.

        Implements stale-while-revalidate pattern:
        - If fresh: return immediately
        - If stale but within grace period: return stale, revalidate in background
        - If expired: compute and return

        Args:
            key: Cache key
            compute_fn: Async function to compute value if not cached
            ttl_seconds: Optional custom TTL

        Returns:
            Cached or computed value
        """
        full_key = f"{self.config.key_prefix}:{key}"
        ttl = ttl_seconds or self.config.ttl_seconds

        try:
            redis = self._get_redis()

            # Try to get from cache
            if isinstance(redis, dict):
                entry = redis.get(full_key)
            else:
                value_json = await redis.get(full_key)
                entry = json.loads(value_json) if value_json else None

            if entry:
                cached_at = entry.get("cached_at", 0)
                expires_at = entry.get("expires_at", 0)
                now = time.time()

                # Fresh - return immediately
                if now < expires_at:
                    self._stats["hits"] += 1
                    return entry["value"]

                # Stale but within grace period - return stale, revalidate in background
                grace_period = self.config.stale_while_revalidate_seconds
                if grace_period > 0 and now < (expires_at + grace_period):
                    self._stats["hits"] += 1
                    # Revalidate in background
                    asyncio.create_task(self._revalidate(key, compute_fn, ttl))
                    return entry["value"]

            # Cache miss or expired - compute
            self._stats["misses"] += 1
            value = await compute_fn()
            await self.set(key, value, ttl)
            return value

        except Exception as e:
            logger.error(f"Cache get_or_compute error for {full_key}: {e}")
            self._stats["errors"] += 1
            # Fallback to computing without cache
            return await compute_fn()

    async def _revalidate(self, key: str, compute_fn: Callable, ttl: int):
        """Revalidate cache entry in background."""
        try:
            value = await compute_fn()
            await self.set(key, value, ttl)
            logger.debug(f"Revalidated cache key: {key}")
        except Exception as e:
            logger.error(f"Cache revalidation error for {key}: {e}")

    def compute_key(self, *args, **kwargs) -> str:
        """
        Compute cache key from arguments.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Hash-based cache key
        """
        # Create a stable string representation
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_str = "|".join(key_parts)

        # Hash for fixed-length key
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0.0

        return {
            **self._stats,
            "hit_rate": round(hit_rate, 3),
            "total_requests": total_requests,
        }

    def clear_stats(self):
        """Clear statistics."""
        self._stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0,
            "errors": 0,
        }

    async def close(self):
        """Close Redis connection."""
        if self._redis_client and not isinstance(self._redis_client, dict):
            try:
                await self._redis_client.close()
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
