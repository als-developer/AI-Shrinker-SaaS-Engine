"""
Structured Logging Module - JSON Format Logging
For centralized log aggregation and analysis
Version: 31.0
"""

import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pythonjsonlogger import jsonlogger
import uuid
import os


class StructuredLogger:
    """Structured JSON logging with correlation IDs"""
    
    _logger = None
    _correlation_id = None
    
    @classmethod
    def setup(cls, service_name: str = "sovereign-grid", log_level: str = "INFO"):
        """Setup structured logging"""
        
        # Create logger
        cls._logger = logging.getLogger(service_name)
        cls._logger.setLevel(getattr(logging, log_level.upper()))
        
        # Remove existing handlers
        cls._logger.handlers.clear()
        
        # Create JSON formatter
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(levelname)s %(name)s %(message)s %(correlation_id)s %(service)s %(environment)s',
            rename_fields={
                'asctime': 'timestamp',
                'levelname': 'level',
                'name': 'logger'
            }
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        cls._logger.addHandler(console_handler)
        
        # File handler (for local debugging)
        file_handler = logging.FileHandler(f'/var/log/{service_name}.log')
        file_handler.setFormatter(formatter)
        cls._logger.addHandler(file_handler)
        
        # Set service and environment in log records
        cls.service_name = service_name
        cls.environment = os.getenv("ENVIRONMENT", "development")
        
        cls.info("Logging system initialized", extra={
            "service": service_name,
            "environment": cls.environment,
            "version": "31.0"
        })
    
    @classmethod
    def set_correlation_id(cls, correlation_id: str):
        """Set correlation ID for request tracing"""
        cls._correlation_id = correlation_id
    
    @classmethod
    def get_correlation_id(cls) -> str:
        """Get current correlation ID"""
        if not cls._correlation_id:
            cls._correlation_id = str(uuid.uuid4())
        return cls._correlation_id
    
    @classmethod
    def _log(cls, level: str, message: str, extra: Dict = None, exc_info: bool = False):
        """Internal logging method"""
        if not cls._logger:
            cls.setup()
        
        log_extra = {
            "correlation_id": cls.get_correlation_id(),
            "service": cls.service_name,
            "environment": cls.environment
        }
        
        if extra:
            log_extra.update(extra)
        
        getattr(cls._logger, level)(message, extra=log_extra, exc_info=exc_info)
    
    @classmethod
    def debug(cls, message: str, extra: Dict = None):
        cls._log("debug", message, extra)
    
    @classmethod
    def info(cls, message: str, extra: Dict = None):
        cls._log("info", message, extra)
    
    @classmethod
    def warning(cls, message: str, extra: Dict = None):
        cls._log("warning", message, extra)
    
    @classmethod
    def error(cls, message: str, extra: Dict = None, exc_info: bool = True):
        cls._log("error", message, extra, exc_info)
    
    @classmethod
    def critical(cls, message: str, extra: Dict = None, exc_info: bool = True):
        cls._log("critical", message, extra, exc_info)
    
    @classmethod
    def log_request(cls, method: str, path: str, status_code: int, duration_ms: float, user_id: str = None):
        """Log HTTP request"""
        cls.info("HTTP Request", extra={
            "http_method": method,
            "http_path": path,
            "http_status": status_code,
            "duration_ms": duration_ms,
            "user_id": user_id
        })
    
    @classmethod
    def log_transaction(cls, tx_id: str, user_id: str, amount_usd: float, status: str):
        """Log financial transaction"""
        cls.info("Transaction processed", extra={
            "transaction_id": tx_id,
            "user_id": user_id,
            "amount_usd": amount_usd,
            "status": status,
            "type": "financial"
        })
    
    @classmethod
    def log_security_event(cls, event_type: str, user_id: str, severity: str, details: Dict):
        """Log security event"""
        cls.warning(f"Security event: {event_type}", extra={
            "security_event_type": event_type,
            "user_id": user_id,
            "severity": severity,
            "details": details
        })
