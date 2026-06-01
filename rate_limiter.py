"""
Rate Limiter - Sliding Window Token Bucket
Distributed rate limiting with Redis
Version: 31.0
"""

import time
import hashlib
from typing import Tuple, Optional
from fastapi import HTTPException, Request
import logging

from core.redis_client import redis_client

logger = logging.getLogger(__name__)


# Rate limit profiles
RATE_LIMIT_PROFILES = {
    "free_tier": {"requests_per_minute": 10, "burst": 15},
    "developer_tier": {"requests_per_minute": 100, "burst": 150},
    "enterprise_tier": {"requests_per_minute": 5000, "burst": 7500},
    "admin_tier": {"requests_per_minute": 10000, "burst": 15000}
}


async def enforce_rate_limit(
    request: Request,
    api_key: Optional[str] = None
) -> Tuple[str, int, int]:
    """
    Enforce rate limiting based on client identifier
    
    Args:
        request: FastAPI request object
        api_key: Optional API key for tier detection
    
    Returns:
        Tuple of (client_id, limit, remaining)
    
    Raises:
        HTTPException 429 if rate limit exceeded
    """
    # Determine client identity
    client_ip = request.client.host if request.client else "unknown"
    
    # Determine tier based on API key
    tier = "free_tier"
    if api_key and api_key.startswith("sk_sov_"):
        # In production, lookup tier from database
        tier = "developer_tier"
    
    # Get limits for this tier
    limits = RATE_LIMIT_PROFILES.get(tier, RATE_LIMIT_PROFILES["free_tier"])
    max_requests = limits["requests_per_minute"]
    
    # Create unique identifier
    client_id = hashlib.sha256(f"{client_ip}:{api_key or ''}".encode()).hexdigest()
    redis_key = f"rate_limit:{client_id}"
    window_seconds = 60
    
    current_time = int(time.time())
    
    try:
        # Use Redis pipeline for atomic operations
        pipeline = redis_client.pipeline()
        
        # Remove old entries
        pipeline.zremrangebyscore(redis_key, 0, current_time - window_seconds)
        
        # Count current requests
        pipeline.zcard(redis_key)
        
        # Add current request
        pipeline.zadd(redis_key, {str(current_time): current_time})
        
        # Set expiration
        pipeline.expire(redis_key, window_seconds + 5)
        
        # Execute pipeline
        _, request_count, _, _ = pipeline.execute()
        
        remaining = max(0, max_requests - request_count)
        
        if request_count > max_requests:
            logger.warning(f"Rate limit exceeded for {client_id[:8]}: {request_count}/{max_requests}")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Limit: {max_requests} requests per minute. Retry after {window_seconds} seconds.",
                headers={"X-RateLimit-Limit": str(max_requests), "X-RateLimit-Remaining": "0"}
            )
        
        return client_id, max_requests, remaining
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rate limiter error: {e}")
        # Fail open - allow request if Redis is down
        return client_id, max_requests, max_requests - 1
