"""
Retry Utilities - Configurable Retry Logic
For handling transient failures in external calls
Version: 31.0
"""

import asyncio
import time
from typing import Callable, Any, Optional, Tuple, Type, Union
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        retry_on_exceptions: Tuple[Type[Exception], ...] = (Exception,),
        retry_on_status_codes: Optional[list] = None
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.retry_on_exceptions = retry_on_exceptions
        self.retry_on_status_codes = retry_on_status_codes or [429, 500, 502, 503, 504]
    
    def should_retry(self, exception: Exception = None, status_code: int = None) -> bool:
        """Determine if retry should be attempted"""
        if exception and isinstance(exception, self.retry_on_exceptions):
            return True
        
        if status_code and status_code in self.retry_on_status_codes:
            return True
        
        return False
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for attempt number"""
        delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))
        return min(delay, self.max_delay)


class RetryExecutor:
    """Execute functions with retry logic"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
    
    async def execute_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function with retry"""
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if not self.config.should_retry(exception=e):
                    raise
                
                if attempt < self.config.max_attempts:
                    delay = self.config.get_delay(attempt)
                    logger.warning(
                        f"Retry {attempt}/{self.config.max_attempts} for {func.__name__} "
                        f"after {delay:.2f}s: {str(e)}"
                    )
                    await asyncio.sleep(delay)
        
        raise last_exception
    
    def execute_sync(self, func: Callable, *args, **kwargs) -> Any:
        """Execute sync function with retry"""
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if not self.config.should_retry(exception=e):
                    raise
                
                if attempt < self.config.max_attempts:
                    delay = self.config.get_delay(attempt)
                    logger.warning(
                        f"Retry {attempt}/{self.config.max_attempts} for {func.__name__} "
                        f"after {delay:.2f}s: {str(e)}"
                    )
                    time.sleep(delay)
        
        raise last_exception


def retry_on_failure(config: Optional[RetryConfig] = None):
    """Decorator for automatic retry on failure"""
    config = config or RetryConfig()
    executor = RetryExecutor(config)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await executor.execute_async(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return executor.execute_sync(func, *args, **kwargs)
        
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
