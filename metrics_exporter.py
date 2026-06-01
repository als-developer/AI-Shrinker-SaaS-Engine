"""
Metrics Exporter - Prometheus Integration
Export system metrics for monitoring and alerting
Version: 31.0
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class MetricsExporter:
    """Prometheus metrics exporter for monitoring"""
    
    # API metrics
    api_requests_total = Counter(
        'api_requests_total',
        'Total API requests',
        ['method', 'endpoint', 'status']
    )
    
    api_request_duration = Histogram(
        'api_request_duration_seconds',
        'API request duration in seconds',
        ['method', 'endpoint']
    )
    
    # Business metrics
    transactions_total = Counter(
        'transactions_total',
        'Total transactions processed',
        ['type', 'currency']
    )
    
    transaction_amount = Counter(
        'transaction_amount_usd_total',
        'Total transaction amount in USD',
        ['type']
    )
    
    # System metrics
    active_users = Gauge(
        'active_users',
        'Number of active users'
    )
    
    active_developers = Gauge(
        'active_developers',
        'Number of active developers'
    )
    
    queue_size = Gauge(
        'queue_size',
        'Size of background task queue',
        ['queue_name']
    )
    
    # Cache metrics
    cache_hits = Counter(
        'cache_hits_total',
        'Total cache hits',
        ['cache_level']
    )
    
    cache_misses = Counter(
        'cache_misses_total',
        'Total cache misses',
        ['cache_level']
    )
    
    @classmethod
    def record_api_request(cls, method: str, endpoint: str, status_code: int, duration: float):
        """Record an API request metric"""
        cls.api_requests_total.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
        cls.api_request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    
    @classmethod
    def record_transaction(cls, transaction_type: str, currency: str, amount_usd: float):
        """Record a transaction metric"""
        cls.transactions_total.labels(type=transaction_type, currency=currency).inc()
        cls.transaction_amount.labels(type=transaction_type).inc(amount_usd)
    
    @classmethod
    def update_active_users(cls, count: int):
        """Update active users gauge"""
        cls.active_users.set(count)
    
    @classmethod
    def update_active_developers(cls, count: int):
        """Update active developers gauge"""
        cls.active_developers.set(count)
    
    @classmethod
    def update_queue_size(cls, queue_name: str, size: int):
        """Update queue size gauge"""
        cls.queue_size.labels(queue_name=queue_name).set(size)
    
    @classmethod
    def record_cache_hit(cls, cache_level: str):
        """Record a cache hit"""
        cls.cache_hits.labels(cache_level=cache_level).inc()
    
    @classmethod
    def record_cache_miss(cls, cache_level: str):
        """Record a cache miss"""
        cls.cache_misses.labels(cache_level=cache_level).inc()
    
    @classmethod
    async def get_metrics(cls) -> Response:
        """Get Prometheus metrics endpoint"""
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    @classmethod
    def get_metrics_dict(cls) -> Dict[str, Any]:
        """Get metrics as dictionary (for internal use)"""
        # This would be more complex in production
        return {
            "api_requests": cls.api_requests_total._value.get(),
            "active_users": cls.active_users._value.get(),
            "active_developers": cls.active_developers._value.get()
        }
