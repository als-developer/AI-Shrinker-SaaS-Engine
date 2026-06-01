"""
Currency Converter - Real-Time Foreign Exchange Rates
Multi-currency conversion with caching
Version: 31.0
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
import logging

from core.cache_manager import CacheManager
from core.redis_client import redis_client

logger = logging.getLogger(__name__)


class CurrencyConverter:
    """Real-time currency conversion with rate caching"""
    
    # Base currency
    BASE_CURRENCY = "USD"
    
    # Supported currencies with fallback rates
    FALLBACK_RATES = {
        "USD": 1.0,
        "TZS": 2615.50,
        "KES": 132.20,
        "UGX": 3765.00,
        "RWF": 1280.00,
        "EUR": 0.92,
        "GBP": 0.78,
        "NGN": 1480.00,
        "ZAR": 18.50,
        "GHS": 12.80
    }
    
    # Cache TTL in seconds
    CACHE_TTL = 3600  # 1 hour
    
    @classmethod
    async def get_rate(cls, from_currency: str, to_currency: str = BASE_CURRENCY) -> float:
        """
        Get exchange rate between currencies
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code (default USD)
            
        Returns:
            Exchange rate
        """
        if from_currency == to_currency:
            return 1.0
        
        cache_key = f"fx_rate:{from_currency}:{to_currency}"
        
        # Check cache
        cached = await redis_client.get(cache_key)
        if cached:
            return float(cached)
        
        # Get rate
        rate = await cls._fetch_rate(from_currency, to_currency)
        
        # Cache for future requests
        await redis_client.setex(cache_key, cls.CACHE_TTL, str(rate))
        
        return rate
    
    @classmethod
    async def _fetch_rate(cls, from_currency: str, to_currency: str) -> float:
        """Fetch rate from API or use fallback"""
        try:
            # Try to fetch from external API
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("rates", {}).get(to_currency, cls.FALLBACK_RATES.get(to_currency, 1.0))
                
        except Exception as e:
            logger.warning(f"Failed to fetch exchange rate: {e}")
        
        # Use fallback rate
        from_rate = cls.FALLBACK_RATES.get(from_currency, 1.0)
        to_rate = cls.FALLBACK_RATES.get(to_currency, 1.0)
        
        if from_currency == cls.BASE_CURRENCY:
            return to_rate
        elif to_currency == cls.BASE_CURRENCY:
            return 1.0 / from_rate
        else:
            return (1.0 / from_rate) * to_rate
    
    @classmethod
    async def convert(
        cls,
        amount: float,
        from_currency: str,
        to_currency: str
    ) -> Dict[str, Any]:
        """
        Convert amount between currencies
        
        Args:
            amount: Amount to convert
            from_currency: Source currency
            to_currency: Target currency
            
        Returns:
            Conversion result with rate and converted amount
        """
        if amount <= 0:
            return {
                "success": False,
                "error": "Amount must be positive",
                "original_amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency
            }
        
        rate = await cls.get_rate(from_currency, to_currency)
        converted_amount = amount * rate
        
        return {
            "success": True,
            "original_amount": amount,
            "from_currency": from_currency.upper(),
            "converted_amount": round(converted_amount, 4),
            "to_currency": to_currency.upper(),
            "rate": round(rate, 6),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @classmethod
    async def get_all_rates(cls, base_currency: str = BASE_CURRENCY) -> Dict[str, float]:
        """Get all exchange rates for a base currency"""
        rates = {}
        
        for currency in cls.FALLBACK_RATES.keys():
            rates[currency] = await cls.get_rate(base_currency, currency)
        
        return rates
    
    @classmethod
    async def refresh_rates(cls):
        """Force refresh of all exchange rates"""
        for from_curr in cls.FALLBACK_RATES.keys():
            cache_key = f"fx_rate:{from_curr}:{cls.BASE_CURRENCY}"
            await redis_client.delete(cache_key)
        
        logger.info("Exchange rates cache cleared")
        return {"status": "refreshed", "timestamp": datetime.utcnow().isoformat()}
