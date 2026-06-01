"""
Custom Decorators - Reusable Function Decorators
For logging, timing, retry logic, and error handling
Version: 31.0
"""

import functools
import time
import logging
from typing import Callable, Any, Optional
from utils.exceptions import SovereignGridException

logger = logging.getLogger(__name__)


def log_execution(func: Callable) -> Callable:
    """Log function execution time and parameters"""
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            duration = (time.perf_counter() - start) * 1000
            logger.debug(f"{func.__name__} completed in {duration:.2f}ms")
            return result
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            logger.error(f"{func.__name__} failed after {duration:.2f}ms: {str(e)}")
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            duration = (time.perf_counter() - start) * 1000
            logger.debug(f"{func.__name__} completed in {duration:.2f}ms")
            return result
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            logger.error(f"{func.__name__} failed after {duration:.2f}ms: {str(e)}")
            raise
    
    import inspect
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """Retry decorator with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        raise
                    
                    logger.warning(f"Retry {attempt + 1}/{max_attempts} for {func.__name__}: {str(e)}")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        raise
                    
                    logger.warning(f"Retry {attempt + 1}/{max_attempts} for {func.__name__}: {str(e)}")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            raise last_exception
        
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def require_role(required_role: str):
    """Decorator to require specific user role"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from context
            from core.auth import get_current_user
            
            user = await get_current_user()
            if user.get("role") != required_role and user.get("role") != "admin":
                raise AuthorizationError(f"Role '{required_role}' required")
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def timeout(seconds: int):
    """Decorator to add timeout to function execution"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")
        
        return wrapper
    
    return decorator


def cached(ttl: int = 300):
    """Decorator to cache function results"""
    def decorator(func: Callable) -> Callable:
        cache = {}
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            import hashlib
            import json
            
            # Create cache key
            key_data = {
                "func": func.__name__,
                "args": str(args),
                "kwargs": str(kwargs)
            }
            key = hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
            
            # Check cache
            if key in cache:
                result, timestamp = cache[key]
                if time.time() - timestamp < ttl:
                    return result
            
            # Execute and cache
            result = await func(*args, **kwargs)
            cache[key] = (result, time.time())
            return result
        
        return wrapper
    
    return decorator


import asyncio
from utils.exceptions import AuthorizationError
