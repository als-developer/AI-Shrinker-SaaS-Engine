"""
Cache Manager - Redis-Based Caching Layer
Multi-level caching with TTL and invalidation
Version: 31.0
"""

import json
import hashlib
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime, timedelta
import logging

from core.redis_client import redis_client

logger = logging.getLogger(__name__)


class CacheManager:
    """Multi-level cache management for API responses and data"""
    
    # Cache levels
    CACHE_LEVELS = {
        "hot": {"ttl": 60},      # 1 minute
        "warm": {"ttl": 300},    # 5 minutes
        "cold": {"ttl": 3600}    # 1 hour
    }
    
    @classmethod
    def _make_key(cls, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and arguments"""
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    @classmethod
    async def get(cls, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = await redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    @classmethod
    async def set(cls, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL"""
        try:
            await redis_client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    @classmethod
    async def delete(cls, key: str) -> bool:
        """Delete key from cache"""
        try:
            await redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    @classmethod
    async def cached(
        cls,
        ttl: int = 300,
        level: str = "warm"
    ):
        """
        Decorator for caching function results
        
        Usage:
            @CacheManager.cached(ttl=60)
            async def expensive_operation(user_id):
                return result
        """
        def decorator(func: Callable[[Any], Awaitable[Any]]):
            async def wrapper(*args, **kwargs):
                # Generate cache key from function name and arguments
                key = cls._make_key(func.__name__, *args, **kwargs)
                
                # Try to get from cache
                cached_result = await cls.get(key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Store in cache
                await cls.set(key, result, ttl)
                
                return result
            return wrapper
        return decorator
    
    @classmethod
    async def get_or_compute(
        cls,
        key: str,
        compute_func: Callable[[], Awaitable[Any]],
        ttl: int = 300
    ) -> Any:
        """Get from cache or compute if missing"""
        result = await cls.get(key)
        if result is not None:
            return result
        
        result = await compute_func()
        await cls.set(key, result, ttl)
        return result
    
    @classmethod
    async def invalidate_pattern(cls, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        try:
            keys = await redis_client.keys(f"*{pattern}*")
            if keys:
                await redis_client.delete(*keys)
                return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return 0
    
    @classmethod
    async def get_stats(cls) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            info = await redis_client.info("stats")
            return {
                "hit_rate": info.get("keyspace_hits", 0) / max(1, info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0)),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "memory_used_mb": info.get("used_memory", 0) / 1024 / 1024
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
    
    @classmethod
    async def warm_up(cls, keys: list, values: list):
        """Warm up cache with predefined keys and values"""
        for key, value in zip(keys, values):
            await cls.set(key, value, ttl=3600)
        logger.info(f"Warmed up {len(keys)} cache entries")
