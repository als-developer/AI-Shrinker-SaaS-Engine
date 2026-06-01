"""
Redis Client - High-Performance Redis Connection Manager
Distributed caching, rate limiting, and queue management
Version: 31.0
"""

import os
import json
from typing import Dict, Any, Optional, List, Union
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis connection manager"""
    
    _client = None
    _config = None
    
    @classmethod
    async def initialize(cls):
        """Initialize Redis connection"""
        if cls._client is not None:
            return
        
        cls._config = {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", 6379)),
            "password": os.getenv("REDIS_PASSWORD", None),
            "db": int(os.getenv("REDIS_DB", 0)),
            "decode_responses": True,
            "max_connections": int(os.getenv("REDIS_MAX_CONNECTIONS", 50))
        }
        
        try:
            cls._client = await redis.from_url(
                f"redis://{cls._config['host']}:{cls._config['port']}/{cls._config['db']}",
                password=cls._config['password'],
                decode_responses=True,
                max_connections=cls._config["max_connections"]
            )
            await cls._client.ping()
            logger.info(f"Redis connected to {cls._config['host']}:{cls._config['port']}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    @classmethod
    async def close(cls):
        """Close Redis connection"""
        if cls._client:
            await cls._client.close()
            cls._client = None
            logger.info("Redis connection closed")
    
    @classmethod
    def _get_client(cls):
        """Get Redis client, initialize if needed"""
        if cls._client is None:
            # Create new event loop for sync contexts
            import asyncio
            loop = asyncio.get_event_loop()
            loop.run_until_complete(cls.initialize())
        return cls._client
    
    # Basic operations
    @classmethod
    async def get(cls, key: str) -> Optional[str]:
        return await cls._get_client().get(key)
    
    @classmethod
    async def set(cls, key: str, value: str, ex: int = None) -> bool:
        return await cls._get_client().set(key, value, ex=ex)
    
    @classmethod
    async def setex(cls, key: str, ttl: int, value: str) -> bool:
        return await cls._get_client().setex(key, ttl, value)
    
    @classmethod
    async def delete(cls, *keys: str) -> int:
        return await cls._get_client().delete(*keys)
    
    @classmethod
    async def exists(cls, key: str) -> bool:
        return await cls._get_client().exists(key) > 0
    
    @classmethod
    async def expire(cls, key: str, ttl: int) -> bool:
        return await cls._get_client().expire(key, ttl)
    
    # Hash operations
    @classmethod
    async def hset(cls, name: str, key: str, value: str) -> int:
        return await cls._get_client().hset(name, key, value)
    
    @classmethod
    async def hget(cls, name: str, key: str) -> Optional[str]:
        return await cls._get_client().hget(name, key)
    
    @classmethod
    async def hgetall(cls, name: str) -> Dict:
        return await cls._get_client().hgetall(name)
    
    @classmethod
    async def hdel(cls, name: str, *keys: str) -> int:
        return await cls._get_client().hdel(name, *keys)
    
    @classmethod
    async def hincrby(cls, name: str, key: str, amount: int = 1) -> int:
        return await cls._get_client().hincrby(name, key, amount)
    
    # Sorted set operations (for rate limiting)
    @classmethod
    async def zadd(cls, key: str, mapping: Dict[str, float]) -> int:
        return await cls._get_client().zadd(key, mapping)
    
    @classmethod
    async def zremrangebyscore(cls, key: str, min_score: float, max_score: float) -> int:
        return await cls._get_client().zremrangebyscore(key, min_score, max_score)
    
    @classmethod
    async def zcard(cls, key: str) -> int:
        return await cls._get_client().zcard(key)
    
    @classmethod
    async def zpopmin(cls, key: str, count: int = 1) -> List:
        return await cls._get_client().zpopmin(key, count)
    
    # List operations (for queues)
    @classmethod
    async def lpush(cls, key: str, *values: str) -> int:
        return await cls._get_client().lpush(key, *values)
    
    @classmethod
    async def rpop(cls, key: str) -> Optional[str]:
        return await cls._get_client().rpop(key)
    
    @classmethod
    async def llen(cls, key: str) -> int:
        return await cls._get_client().llen(key)
    
    # Pub/Sub
    @classmethod
    async def publish(cls, channel: str, message: str) -> int:
        return await cls._get_client().publish(channel, message)
    
    @classmethod
    async def subscribe(cls, channel: str):
        pubsub = cls._get_client().pubsub()
        await pubsub.subscribe(channel)
        return pubsub
    
    # Utility
    @classmethod
    async def ping(cls) -> bool:
        return await cls._get_client().ping()
    
    @classmethod
    async def info(cls, section: str = None) -> Dict:
        return await cls._get_client().info(section)
    
    @classmethod
    async def keys(cls, pattern: str) -> List:
        return await cls._get_client().keys(pattern)


# Export singleton instance
redis_client = RedisClient()
