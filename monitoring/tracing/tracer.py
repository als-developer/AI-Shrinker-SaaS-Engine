"""
Distributed Tracing Module - OpenTelemetry Integration
For tracing requests across microservices
Version: 31.0
"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
import os
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class TracingManager:
    """OpenTelemetry distributed tracing setup"""
    
    _initialized = False
    _tracer = None
    
    @classmethod
    def initialize(cls, service_name: str = "sovereign-grid"):
        """Initialize OpenTelemetry tracing"""
        if cls._initialized:
            return
        
        # Set up resource
        resource = Resource(attributes={
            SERVICE_NAME: service_name,
            "service.version": "31.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "development")
        })
        
        # Set up tracer provider
        provider = TracerProvider(resource=resource)
        
        # Configure Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=os.getenv("JAEGER_AGENT_HOST", "localhost"),
            agent_port=int(os.getenv("JAEGER_AGENT_PORT", 6831)),
        )
        
        # Add span processor
        provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        
        # Set global tracer provider
        trace.set_tracer_provider(provider)
        
        cls._tracer = trace.get_tracer(__name__)
        cls._initialized = True
        logger.info(f"Tracing initialized for {service_name}")
    
    @classmethod
    def instrument_app(cls, app):
        """Instrument FastAPI application"""
        if cls._initialized:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI instrumented for tracing")
    
    @classmethod
    def instrument_redis(cls):
        """Instrument Redis client"""
        if cls._initialized:
            RedisInstrumentor().instrument()
            logger.info("Redis instrumented for tracing")
    
    @classmethod
    def instrument_httpx(cls):
        """Instrument HTTPX client"""
        if cls._initialized:
            HTTPXClientInstrumentor().instrument()
            logger.info("HTTPX instrumented for tracing")
    
    @classmethod
    def get_tracer(cls):
        """Get the tracer instance"""
        if not cls._initialized:
            cls.initialize()
        return cls._tracer
    
    @classmethod
    def trace_function(cls, name: str = None):
        """Decorator to trace function execution"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                tracer = cls.get_tracer()
                span_name = name or func.__name__
                with tracer.start_as_current_span(span_name):
                    # Add function arguments as attributes (sanitized)
                    span = trace.get_current_span()
                    if span:
                        span.set_attribute("function.name", func.__name__)
                        span.set_attribute("function.module", func.__module__)
                    return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    @classmethod
    async def create_span(cls, name: str, attributes: dict = None):
        """Create a custom span"""
        tracer = cls.get_tracer()
        with tracer.start_as_current_span(name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            yield span
    
    @classmethod
    def add_event(cls, name: str, attributes: dict = None):
        """Add an event to current span"""
        span = trace.get_current_span()
        if span:
            span.add_event(name, attributes)
    
    @classmethod
    def set_attribute(cls, key: str, value):
        """Set attribute on current span"""
        span = trace.get_current_span()
        if span:
            span.set_attribute(key, value)
    
    @classmethod
    def set_error(cls, error: Exception):
        """Record error on current span"""
        span = trace.get_current_span()
        if span:
            span.record_exception(error)
            span.set_status(trace.StatusCode.ERROR, str(error))
