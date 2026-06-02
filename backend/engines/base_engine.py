from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import json

from ..services.cache_service import CacheService
from ..utils.logger import get_logger

class BaseEngine(ABC):
    """Base class for all engines"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(name)
        self.cache = CacheService()
    
    @abstractmethod
    async def process(self, **kwargs) -> Dict[str, Any]:
        """Process the request"""
        pass
    
    async def _cache_get(self, key: str) -> Optional[Dict]:
        """Get from cache"""
        data = await self.cache.get(f"{self.name}:{key}")
        return json.loads(data) if data else None
    
    async def _cache_set(self, key: str, value: Dict, ttl: int = 3600):
        """Set in cache"""
        await self.cache.set(f"{self.name}:{key}", json.dumps(value), ttl)
    
    def _log(self, level: str, message: str, **kwargs):
        """Log message"""
        getattr(self.logger, level)(f"[{self.name}] {message}", extra=kwargs)
    
    async def health_check(self) -> bool:
        """Check engine health"""
        return await self.cache.health_check()
