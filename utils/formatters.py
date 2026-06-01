"""
Data Formatters - Formatting Utilities for Output
For formatting currency, dates, phone numbers, and JSON
Version: 31.0
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import re


class DataFormatter:
    """Data formatting utilities"""
    
    # Currency symbols
    CURRENCY_SYMBOLS = {
        "USD": "$",
        "TZS": "TSh",
        "KES": "KSh",
        "EUR": "€",
        "GBP": "£",
        "NGN": "₦",
        "ZAR": "R"
    }
    
    @classmethod
    def format_currency(cls, amount: float, currency: str = "USD", include_symbol: bool = True) -> str:
        """
        Format currency amount
        
        Args:
            amount: Amount to format
            currency: Currency code
            include_symbol: Include currency symbol
        
        Returns:
            Formatted currency string
        """
        symbol = cls.CURRENCY_SYMBOLS.get(currency.upper(), currency.upper())
        
        # Format based on currency
        if currency.upper() == "TZS":
            formatted = f"{amount:,.0f}"
        else:
            formatted = f"{amount:,.2f}"
        
        if include_symbol:
            return f"{symbol} {formatted}".strip()
        
        return formatted
    
    @classmethod
    def format_date(cls, date: datetime, format_type: str = "standard") -> str:
        """
        Format datetime
        
        Args:
            date: Datetime object
            format_type: standard, iso, short, full
        
        Returns:
            Formatted date string
        """
        formats = {
            "standard": "%Y-%m-%d %H:%M:%S",
            "iso": "%Y-%m-%dT%H:%M:%SZ",
            "short": "%Y-%m-%d",
            "full": "%A, %B %d, %Y at %I:%M %p",
            "time": "%I:%M %p",
            "date": "%B %d, %Y"
        }
        
        fmt = formats.get(format_type, formats["standard"])
        return date.strftime(fmt)
    
    @classmethod
    def format_phone(cls, phone: str, country: str = "TZ") -> str:
        """
        Format phone number for display
        
        Args:
            phone: Raw phone number
            country: Country code
        
        Returns:
            Formatted phone number
        """
        import phonenumbers
        
        try:
            parsed = phonenumbers.parse(phone, country)
            return phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )
        except Exception:
            return phone
    
    @classmethod
    def format_bytes(cls, bytes_count: int) -> str:
        """
        Format bytes to human readable
        
        Args:
            bytes_count: Number of bytes
        
        Returns:
            Human readable size
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} PB"
    
    @classmethod
    def format_duration(cls, seconds: float) -> str:
        """
        Format duration in seconds to human readable
        
        Args:
            seconds: Duration in seconds
        
        Returns:
            Human readable duration
        """
        if seconds < 60:
            return f"{seconds:.0f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.0f} minutes"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.1f} hours"
        else:
            days = seconds / 86400
            return f"{days:.1f} days"
    
    @classmethod
    def format_percent(cls, value: float, decimals: int = 1) -> str:
        """Format as percentage"""
        return f"{value * 100:.{decimals}f}%"
    
    @classmethod
    def truncate_text(cls, text: str, max_length: int = 100, suffix: str = "...") -> str:
        """Truncate text to maximum length"""
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @classmethod
    def slugify(cls, text: str) -> str:
        """Convert text to URL-friendly slug"""
        text = text.lower()
        text = re.sub(r'[^a-z0-9]+', '-', text)
        text = text.strip('-')
        return text
    
    @classmethod
    def pretty_json(cls, data: Any, indent: int = 2) -> str:
        """Format JSON with pretty printing"""
        try:
            return json.dumps(data, indent=indent, default=str)
        except Exception:
            return str(data)
    
    @classmethod
    def mask_string(cls, value: str, visible_start: int = 4, visible_end: int = 4) -> str:
        """Mask a string with asterisks"""
        if not value or len(value) <= visible_start + visible_end:
            return "*" * 8
        
        start = value[:visible_start]
        end = value[-visible_end:] if visible_end > 0 else ""
        middle = "*" * min(8, len(value) - visible_start - visible_end)
        
        return f"{start}{middle}{end}"
