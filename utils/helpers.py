"""
Helper Functions - Common Utilities
For string manipulation, hashing, ID generation, and more
Version: 31.0
"""

import uuid
import secrets
import hashlib
import random
import string
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta


class Helpers:
    """General helper functions"""
    
    @staticmethod
    def generate_id(prefix: str = "", length: int = 12) -> str:
        """Generate a unique ID with optional prefix"""
        unique_id = uuid.uuid4().hex[:length]
        if prefix:
            return f"{prefix}_{unique_id}"
        return unique_id
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a cryptographically secure token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """Generate a numeric OTP"""
        return ''.join([str(random.randint(0, 9)) for _ in range(length)])
    
    @staticmethod
    def hash_string(data: str, algorithm: str = "sha256") -> str:
        """Hash a string using specified algorithm"""
        algorithms = {
            "md5": hashlib.md5,
            "sha1": hashlib.sha1,
            "sha256": hashlib.sha256,
            "sha512": hashlib.sha512
        }
        
        hash_func = algorithms.get(algorithm, hashlib.sha256)
        return hash_func(data.encode()).hexdigest()
    
    @staticmethod
    def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """Truncate string to maximum length"""
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def pluralize(word: str, count: int, plural: Optional[str] = None) -> str:
        """Return plural or singular form based on count"""
        if count == 1:
            return word
        
        if plural:
            return plural
        
        # Basic pluralization rules
        if word.endswith('y'):
            return word[:-1] + 'ies'
        elif word.endswith(('s', 'x', 'z', 'ch', 'sh')):
            return word + 'es'
        else:
            return word + 's'
    
    @staticmethod
    def dict_merge(dict1: Dict, dict2: Dict) -> Dict:
        """Recursively merge two dictionaries"""
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = Helpers.dict_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def chunk_list(lst: List, chunk_size: int) -> List[List]:
        """Split a list into chunks"""
        return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
    
    @staticmethod
    def get_client_ip(request) -> str:
        """Extract client IP address from request"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    @staticmethod
    def format_timedelta(delta: timedelta) -> str:
        """Format timedelta for human readability"""
        seconds = int(delta.total_seconds())
        
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if secs > 0 or not parts:
            parts.append(f"{secs}s")
        
        return " ".join(parts)
    
    @staticmethod
    def is_valid_json(value: str) -> bool:
        """Check if string is valid JSON"""
        import json
        try:
            json.loads(value)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    @staticmethod
    def safe_json_parse(value: str, default: Any = None) -> Any:
        """Safely parse JSON with fallback"""
        import json
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return default
    
    @staticmethod
    def bool_from_string(value: str) -> bool:
        """Convert string to boolean"""
        if isinstance(value, bool):
            return value
        
        if not value:
            return False
        
        return value.lower() in ("true", "yes", "1", "on", "enabled")
