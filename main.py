"""
Sovereign Omniscience Grid - Production Main Entry Point
Version: 31.0 | Production Ready | Billion User Scale
"""

import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import logging

from api.routes import router as api_router
from middleware.logging_middleware import LoggingMiddleware
from middleware.request_id_middleware import RequestIDMiddleware
from middleware.error_handler import global_exception_handler
from core.telemetry import TelemetryManager
from core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global telemetry instance
telemetry = TelemetryManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("🚀 Sovereign Grid starting up...")
    await telemetry.start()
    logger.info("✅ Telemetry initialized")
    
    # Start background workers
    asyncio.create_task(start_background_workers())
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Sovereign Grid...")
    await telemetry.stop()
    logger.info("✅ Clean shutdown complete")


async def start_background_workers():
    """Launch async background workers"""
    from workers.queue_worker import QueueWorker
    from workers.email_worker import EmailWorker
    from workers.webhook_worker import WebhookWorker
    
    workers = [
        QueueWorker(),
        EmailWorker(),
        WebhookWorker()
    ]
    
    await asyncio.gather(*[w.start() for w in workers])


# Initialize FastAPI app
app = FastAPI(
    title="Sovereign Omniscience Grid",
    description="Tier-0 Lockless Multi-Core Engine for Global Validation, Payments & AI Optimization",
    version="31.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)

# Register exception handlers
app.add_exception_handler(Exception, global_exception_handler)

# Include routers
app.include_router(api_router, prefix="/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "31.0",
        "region": os.getenv("CLOUD_REGION_NODE", "GLOBAL_MESH_NODE_1")
    }

# Readiness probe
@app.get("/ready")
async def readiness_check():
    return {"status": "ready"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        loop="uvloop",
        http="httptools"
    )
