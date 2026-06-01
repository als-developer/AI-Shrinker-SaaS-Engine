"""
Health Check System - Comprehensive Service Health Monitoring
For Kubernetes liveness and readiness probes
Version: 31.0
"""

import asyncio
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
import logging
import os

from core.supabase_client import supabase
from core.redis_client import redis_client
from core.db_pool import DatabasePool

logger = logging.getLogger(__name__)


class HealthChecker:
    """Comprehensive health checking for all services"""
    
    @classmethod
    async def check_database(cls) -> Tuple[bool, str, float]:
        """Check database connectivity and latency"""
        start_time = datetime.utcnow()
        try:
            # Simple query to test connection
            result = await supabase.table_select("health_check", {})
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            return True, "Database connected", latency
        except Exception as e:
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            return False, f"Database error: {str(e)}", latency
    
    @classmethod
    async def check_redis(cls) -> Tuple[bool, str, float]:
        """Check Redis connectivity and latency"""
        start_time = datetime.utcnow()
        try:
            await redis_client.ping()
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            return True, "Redis connected", latency
        except Exception as e:
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            return False, f"Redis error: {str(e)}", latency
    
    @classmethod
    async def check_api_rate_limits(cls) -> Tuple[bool, str, float]:
        """Check rate limiting functionality"""
        start_time = datetime.utcnow()
        try:
            # Test rate limit storage
            test_key = "health_test:rate_limit"
            await redis_client.setex(test_key, 10, "test")
            value = await redis_client.get(test_key)
            await redis_client.delete(test_key)
            
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            if value == "test":
                return True, "Rate limiting operational", latency
            return False, "Rate limiting storage failed", latency
        except Exception as e:
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            return False, f"Rate limit error: {str(e)}", latency
    
    @classmethod
    async def check_webhook_dispatcher(cls) -> Tuple[bool, str, float]:
        """Check webhook dispatcher health"""
        start_time = datetime.utcnow()
        try:
            # Check if queue is responsive
            queue_size = await redis_client.llen("webhook_queue")
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            return True, f"Webhook dispatcher active (queue: {queue_size})", latency
        except Exception as e:
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            return False, f"Webhook error: {str(e)}", latency
    
    @classmethod
    async def check_background_workers(cls) -> Tuple[bool, str, float]:
        """Check background worker health"""
        start_time = datetime.utcnow()
        try:
            # Check worker heartbeat
            last_heartbeat = await redis_client.get("worker:heartbeat:last")
            if last_heartbeat:
                last_time = datetime.fromisoformat(last_heartbeat)
                if datetime.utcnow() - last_time < timedelta(minutes=5):
                    latency = (datetime.utcnow() - start_time).total_seconds() * 1000
                    return True, "Workers healthy", latency
            
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            return False, "No worker heartbeat detected", latency
        except Exception as e:
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            return False, f"Worker check error: {str(e)}", latency
    
    @classmethod
    async def full_health_check(cls) -> Dict[str, Any]:
        """
        Run full health check on all services        
        Returns:
            Comprehensive health status
        """
        checks = {
            "database": await cls.check_database(),
            "redis": await cls.check_redis(),
            "rate_limits": await cls.check_api_rate_limits(),
            "webhook_dispatcher": await cls.check_webhook_dispatcher(),
            "background_workers": await cls.check_background_workers()
        }
        
        # Calculate overall status
        all_healthy = all(status for status, _, _ in checks.values())
        
        # Calculate overall latency
        total_latency = sum(latency for _, _, latency in checks.values())
        avg_latency = total_latency / len(checks)
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "31.0",
            "region": os.getenv("CLOUD_REGION_NODE", "GLOBAL_MESH_NODE_1"),
            "latency_ms": round(avg_latency, 2),
            "checks": {
                name: {
                    "healthy": healthy,
                    "message": message,
                    "latency_ms": round(latency, 2)
                }
                for name, (healthy, message, latency) in checks.items()
            }
        }
    
    @classmethod
    async def liveness_check(cls) -> Dict[str, Any]:
        """Simple liveness check (Kubernetes liveness probe)"""
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @classmethod
    async def readiness_check(cls) -> Dict[str, Any]:
        """Readiness check (Kubernetes readiness probe)"""
        result = await cls.full_health_check()
        return {
            "status": "ready" if result["status"] == "healthy" else "not_ready",
            "checks": result["checks"]
        }
