"""
Health Check Endpoints - FastAPI Routes for Health Monitoring
Exposes health, readiness, and metrics endpoints
Version: 31.0
"""

from fastapi import APIRouter, Response
from monitoring.health.checker import HealthChecker
from monitoring.prometheus.metrics import MetricsCollector
import json

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Basic health check endpoint (Kubernetes liveness)"""
    return await HealthChecker.liveness_check()


@router.get("/ready")
async def readiness_check():
    """Readiness probe endpoint (Kubernetes readiness)"""
    return await HealthChecker.readiness_check()


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with all dependencies"""
    return await HealthChecker.full_health_check()


@router.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/metrics/health")
async def metrics_health_check():
    """Health metrics summary for monitoring"""
    health = await HealthChecker.full_health_check()
    
    # Update Prometheus gauges based on health
    if health["status"] == "healthy":
        MetricsCollector.active_users.labels(tier="system").set(1)
    else:
        MetricsCollector.active_users.labels(tier="system").set(0)
    
    return {
        "status": health["status"],
        "healthy_services": sum(1 for c in health["checks"].values() if c["healthy"]),
        "total_services": len(health["checks"]),
        "average_latency_ms": health["latency_ms"]
    }


@router.get("/version")
async def version_info():
    """Version information endpoint"""
    return {
        "version": "31.0",
        "api_version": "v1",
        "build_date": "2026-05-31",
        "environment": os.getenv("ENVIRONMENT", "development")
    }


import os
