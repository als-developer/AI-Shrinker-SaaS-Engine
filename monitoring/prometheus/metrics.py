"""
Prometheus Metrics Collection - Custom Business & System Metrics
For monitoring API performance, business KPIs, and system health
Version: 31.0
"""

from prometheus_client import Counter, Histogram, Gauge, Summary, Info
from typing import Dict, Any, Optional
import time
import functools
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Centralized metrics collection for Prometheus"""
    
    # API Metrics
    api_requests_total = Counter(
        'sovereign_api_requests_total',
        'Total number of API requests',
        ['method', 'endpoint', 'status', 'engine']
    )
    
    api_request_duration = Histogram(
        'sovereign_api_request_duration_seconds',
        'API request duration in seconds',
        ['method', 'endpoint', 'engine'],
        buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)
    )
    
    # Business Metrics
    transactions_total = Counter(
        'sovereign_transactions_total',
        'Total number of transactions processed',
        ['type', 'currency', 'status']
    )
    
    transaction_amount = Counter(
        'sovereign_transaction_amount_usd_total',
        'Total transaction amount in USD',
        ['type']
    )
    
    # AI Model Metrics
    model_compressions_total = Counter(
        'sovereign_model_compressions_total',
        'Total number of AI model compressions',
        ['model_size', 'precision', 'status']
    )
    
    compression_duration = Histogram(
        'sovereign_compression_duration_seconds',
        'Model compression duration in seconds',
        ['model_size', 'precision'],
        buckets=(60, 300, 600, 1800, 3600, 7200)
    )
    
    # User Metrics
    active_users = Gauge(
        'sovereign_active_users',
        'Number of active users',
        ['tier']
    )
    
    active_developers = Gauge(
        'sovereign_active_developers',
        'Number of active developers'
    )
    
    # System Metrics
    queue_size = Gauge(
        'sovereign_queue_size',
        'Size of processing queues',
        ['queue_name']
    )
    
    database_connections = Gauge(
        'sovereign_database_connections',
        'Number of active database connections',
        ['pool']
    )
    
    redis_connections = Gauge(
        'sovereign_redis_connections',
        'Number of active Redis connections'
    )
    
    # Cache Metrics
    cache_hits_total = Counter(
        'sovereign_cache_hits_total',
        'Total cache hits',
        ['cache_level', 'operation']
    )
    
    cache_misses_total = Counter(
        'sovereign_cache_misses_total',
        'Total cache misses',
        ['cache_level', 'operation']
    )
    
    cache_size_bytes = Gauge(
        'sovereign_cache_size_bytes',
        'Cache size in bytes',
        ['cache_level']
    )
    
    # Rate Limit Metrics
    rate_limit_hits_total = Counter(
        'sovereign_rate_limit_hits_total',
        'Total rate limit hits',
        ['tier', 'endpoint']
    )
    
    # SLA Metrics
    sla_violations_total = Counter(
        'sovereign_sla_violations_total',
        'Total SLA violations',
        ['org_tier', 'violation_type']
    )
    
    # Info metric
    system_info = Info('sovereign_system', 'System information')
    
    @classmethod
    def record_api_request(cls, method: str, endpoint: str, status_code: int, duration: float, engine: str = "unknown"):
        """Record an API request metric"""
        cls.api_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status_code),
            engine=engine
        ).inc()
        
        cls.api_request_duration.labels(
            method=method,
            endpoint=endpoint,
            engine=engine
        ).observe(duration)
    
    @classmethod
    def record_transaction(cls, tx_type: str, currency: str, amount_usd: float, status: str = "success"):
        """Record a transaction metric"""
        cls.transactions_total.labels(
            type=tx_type,
            currency=currency,
            status=status
        ).inc()
        
        if status == "success":
            cls.transaction_amount.labels(type=tx_type).inc(amount_usd)
    
    @classmethod
    def record_compression(cls, model_size: str, precision: str, duration: float, status: str = "success"):
        """Record a model compression metric"""
        cls.model_compressions_total.labels(
            model_size=model_size,
            precision=precision,
            status=status
        ).inc()
        
        if status == "success":
            cls.compression_duration.labels(
                model_size=model_size,
                precision=precision
            ).observe(duration)
    
    @classmethod
    def update_active_users(cls, count: int, tier: str = "all"):
        """Update active users gauge"""
        cls.active_users.labels(tier=tier).set(count)
    
    @classmethod
    def update_active_developers(cls, count: int):
        """Update active developers gauge"""
        cls.active_developers.set(count)
    
    @classmethod
    def update_queue_size(cls, queue_name: str, size: int):
        """Update queue size gauge"""
        cls.queue_size.labels(queue_name=queue_name).set(size)
    
    @classmethod
    def record_cache_hit(cls, cache_level: str, operation: str = "get"):
        """Record a cache hit"""
        cls.cache_hits_total.labels(cache_level=cache_level, operation=operation).inc()
    
    @classmethod
    def record_cache_miss(cls, cache_level: str, operation: str = "get"):
        """Record a cache miss"""
        cls.cache_misses_total.labels(cache_level=cache_level, operation=operation).inc()
    
    @classmethod
    def record_rate_limit(cls, tier: str, endpoint: str):
        """Record a rate limit hit"""
        cls.rate_limit_hits_total.labels(tier=tier, endpoint=endpoint).inc()
    
    @classmethod
    def record_sla_violation(cls, org_tier: str, violation_type: str):
        """Record an SLA violation"""
        cls.sla_violations_total.labels(org_tier=org_tier, violation_type=violation_type).inc()
    
    @classmethod
    def set_system_info(cls, version: str, environment: str, region: str):
        """Set system information metric"""
        cls.system_info.info({
            "version": version,
            "environment": environment,
            "region": region,
            "deployed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    @classmethod
    def monitor_execution(cls, metric_name: str, **labels):
        """Decorator to monitor function execution time"""
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.perf_counter() - start_time
                    
                    # Record duration metric
                    if hasattr(cls, metric_name):
                        metric = getattr(cls, metric_name)
                        if isinstance(metric, Histogram):
                            metric.labels(**labels).observe(duration)
                    
                    return result
                except Exception as e:
                    duration = time.perf_counter() - start_time
                    logger.error(f"Function {func.__name__} failed after {duration:.2f}s: {e}")
                    raise
            return wrapper
        return decorator
