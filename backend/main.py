from fastapi import FastAPI, HTTPException, Depends, Header, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import time
import uuid
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from engines.truth_engine import TruthEngine
from engines.centpay_engine import CentPayEngine
from engines.ai_shrinker import AIShrinkerEngine
from engines.deepfake_engine import DeepfakeEngine
from engines.translator_engine import TranslatorEngine
from middleware.auth import verify_api_key, rate_limit
from middleware.logging import log_request, LoggingMiddleware
from database.models import init_db, get_db
from services.cache_service import CacheService
from services.metrics_service import MetricsService
from config.settings import Settings
from utils.logger import setup_logger

# Initialize
settings = Settings()
logger = setup_logger()
cache_service = CacheService()
metrics_service = MetricsService()

app = FastAPI(
    title="Sovereign OmniCore",
    description="Ultimate 5-in-1 AI Platform: TruthEngine, CentPay, AI Shrinker, Deepfake Detector, Cultural Translator",
    version="5.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

# Initialize engines
truth_engine = TruthEngine()
centpay_engine = CentPayEngine()
ai_shrinker = AIShrinkerEngine()
deepfake_engine = DeepfakeEngine()
translator_engine = TranslatorEngine()

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    await init_db()
    await cache_service.connect()
    await metrics_service.init()
    logger.info("Sovereign OmniCore started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await cache_service.disconnect()
    logger.info("Sovereign OmniCore shutting down")

@app.get("/")
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "5.0.0",
        "engines": ["truth", "centpay", "ai_shrinker", "deepfake", "translator"],
        "cache": await cache_service.health_check(),
        "uptime": time.time() - app.start_time if hasattr(app, 'start_time') else 0
    }

@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    return await metrics_service.get_all_metrics()

# ==================== ENGINE 1: TRUTH ENGINE ====================

@app.post("/api/v1/truth/verify")
@rate_limit(max_requests=100, window=60)
async def truth_verify(
    request: Dict[str, str],
    api_key: str = Depends(verify_api_key),
    background_tasks: BackgroundTasks = None
):
    """Verify if text claims are true or AI hallucinations"""
    text = request.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Text required")
    
    start_time = time.time()
    result = await truth_engine.verify(text)
    result["processing_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    # Track metrics
    await metrics_service.increment_counter("truth_verifications_total")
    await metrics_service.record_histogram("truth_processing_time_ms", result["processing_time_ms"])
    
    # Background logging
    if background_tasks:
        background_tasks.add_task(truth_engine.log_verification, text, result)
    
    return JSONResponse(content=result)

@app.post("/api/v1/truth/batch")
async def truth_batch(
    request: Dict[str, List[str]],
    api_key: str = Depends(verify_api_key)
):
    """Batch verify multiple texts"""
    texts = request.get("texts", [])
    if not texts or len(texts) > 100:
        raise HTTPException(status_code=400, detail="1-100 texts required")
    
    start_time = time.time()
    results = await truth_engine.batch_verify(texts)
    
    return {
        "results": results,
        "total_processed": len(results),
        "processing_time_ms": round((time.time() - start_time) * 1000, 2)
    }

@app.get("/api/v1/truth/stats")
async def truth_stats(api_key: str = Depends(verify_api_key)):
    """Get truth engine statistics"""
    return await truth_engine.get_stats()

# ==================== ENGINE 2: CENTPAY ====================

@app.post("/api/v1/payments/charge")
@rate_limit(max_requests=1000, window=60)
async def payment_charge(
    request: Dict[str, Any],
    api_key: str = Depends(verify_api_key)
):
    """Process micro-payment (sentimo)"""
    user_id = request.get("user_id")
    merchant_id = request.get("merchant_id")
    amount_tzs = request.get("amount_tzs")
    
    if not all([user_id, merchant_id, amount_tzs]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    if amount_tzs <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    start_time = time.time()
    result = await centpay_engine.charge(user_id, merchant_id, amount_tzs)
    result["processing_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    if result["status"] == "success":
        await metrics_service.increment_counter("payments_successful_total")
        await metrics_service.increment_counter("payments_volume_tzs", int(amount_tzs))
    else:
        await metrics_service.increment_counter("payments_failed_total")
    
    return JSONResponse(content=result)

@app.get("/api/v1/payments/balance/{user_id}")
async def get_balance(
    user_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get user wallet balance"""
    balance = await centpay_engine.get_balance(user_id)
    return balance

@app.post("/api/v1/payments/topup")
async def topup_wallet(
    request: Dict[str, Any],
    api_key: str = Depends(verify_api_key)
):
    """Top up wallet balance"""
    user_id = request.get("user_id")
    amount_tzs = request.get("amount_tzs")
    
    if not user_id or not amount_tzs:
        raise HTTPException(status_code=400, detail="user_id and amount_tzs required")
    
    result = await centpay_engine.topup(user_id, amount_tzs)
    return result

@app.get("/api/v1/payments/transactions/{user_id}")
async def get_transactions(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    api_key: str = Depends(verify_api_key)
):
    """Get user transaction history"""
    transactions = await centpay_engine.get_transactions(user_id, limit, offset)
    return {"transactions": transactions, "total": len(transactions)}

# ==================== ENGINE 3: AI SHRINKER ====================

@app.post("/api/v1/ai/shrink")
async def shrink_model(
    request: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    background_tasks: BackgroundTasks = None
):
    """Compress AI model by 10x"""
    model_name = request.get("model_name")
    precision = request.get("precision", "int4")
    
    if not model_name:
        raise HTTPException(status_code=400, detail="model_name required")
    
    if precision not in ["int4", "int8", "fp16", "int2", "binary"]:
        raise HTTPException(status_code=400, detail="Invalid precision")
    
    result = await ai_shrinker.compress(model_name, precision)
    
    if background_tasks:
        background_tasks.add_task(ai_shrinker.process_compression, result["job_id"], model_name, precision)
    
    await metrics_service.increment_counter("shrink_jobs_total")
    
    return result

@app.get("/api/v1/ai/status/{job_id}")
async def get_shrink_status(
    job_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get compression job status"""
    status = await ai_shrinker.get_status(job_id)
    return status

@app.get("/api/v1/ai/models")
async def list_models(api_key: str = Depends(verify_api_key)):
    """List available models for compression"""
    models = await ai_shrinker.list_models()
    return {"models": models}

# ==================== ENGINE 4: DEEPFAKE DETECTOR ====================

@app.post("/api/v1/deepfake/detect")
async def detect_deepfake(
    request: Dict[str, Any],
    api_key: str = Depends(verify_api_key)
):
    """Detect AI-generated voice or video"""
    audio_samples = request.get("audio_samples", [])
    
    if not audio_samples:
        raise HTTPException(status_code=400, detail="audio_samples required")
    
    if len(audio_samples) < 10:
        raise HTTPException(status_code=400, detail="At least 10 samples required")
    
    start_time = time.time()
    result = await deepfake_engine.detect(audio_samples)
    result["processing_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    await metrics_service.increment_counter("deepfake_scans_total")
    if result["risk_score"] > 70:
        await metrics_service.increment_counter("deepfake_detected_total")
    
    return result

@app.post("/api/v1/deepfake/upload")
async def upload_media(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Upload and analyze media file"""
    job_id = f"df_{uuid.uuid4().hex[:16]}"
    
    # In production, handle file upload
    return {
        "status": "processing",
        "job_id": job_id,
        "estimated_time_seconds": 10
    }

@app.get("/api/v1/deepfake/result/{job_id}")
async def get_deepfake_result(
    job_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get deepfake analysis result"""
    result = await deepfake_engine.get_result(job_id)
    return result

# ==================== ENGINE 5: CULTURAL TRANSLATOR ====================

@app.post("/api/v1/translate/cultural")
async def cultural_translate(
    request: Dict[str, Any],
    api_key: str = Depends(verify_api_key)
):
    """Translate with cultural context awareness"""
    text = request.get("text")
    target_country = request.get("target_country")
    source_lang = request.get("source_language", "auto")
    
    if not text or not target_country:
        raise HTTPException(status_code=400, detail="text and target_country required")
    
    if len(text) > 10000:
        raise HTTPException(status_code=400, detail="Text too long (max 10000 chars)")
    
    start_time = time.time()
    result = await translator_engine.translate(text, target_country, source_lang)
    result["processing_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    await metrics_service.increment_counter("translations_total")
    if result["risk_score"] > 50:
        await metrics_service.increment_counter("translations_risky_total")
    
    return result

@app.get("/api/v1/translate/risks/{country}")
async def get_cultural_risks(
    country: str,
    api_key: str = Depends(verify_api_key)
):
    """Get cultural risks for specific country"""
    risks = await translator_engine.get_risks(country)
    return risks

@app.get("/api/v1/translate/countries")
async def list_countries(api_key: str = Depends(verify_api_key)):
    """List supported countries"""
    countries = await translator_engine.list_countries()
    return {"countries": countries}

if __name__ == "__main__":
    app.start_time = time.time()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=settings.WORKERS_COUNT
    )
