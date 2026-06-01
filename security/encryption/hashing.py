"""
Cryptographic Hashing Module - SHA-256, SHA-512, BLAKE2
For secure data integrity and password hashing
Version: 31.0
"""

import hashlib
import hmac
import secrets
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class CryptoHashing:
    """Cryptographic hashing utilities"""
    
    @staticmethod
    def sha256(data: str) -> str:
        """Generate SHA-256 hash"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def sha512(data: str) -> str:
        """Generate SHA-512 hash"""
        return hashlib.sha512(data.encode()).hexdigest()
    
    @staticmethod
    def blake2b(data: str, digest_size: int = 32) -> str:
        """Generate BLAKE2b hash (faster than SHA)"""
        return hashlib.blake2b(data.encode(), digest_size=digest_size).hexdigest()
    
    @staticmethod
    def hmac_sha256(key: str, message: str) -> str:
        """Generate HMAC-SHA256"""
        return hmac.new(
            key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
    
    @classmethod
    def hash_api_key(cls, raw_key: str) -> str:
        """Hash API key for storage (use SHA-256)"""
        if not raw_key.startswith("sk_sov_"):
            raise ValueError("Invalid API key format")
        return cls.sha256(raw_key)
    
    @classmethod
    def hash_with_salt(cls, data: str) -> Tuple[str, str]:
        """
        Hash data with random salt
        
        Args:
            data: Data to hash
        
        Returns:
            Tuple of (hashed_data, salt)
        """
        salt = secrets.token_hex(16)
        salted_data = data + salt
        hashed = cls.sha256(salted_data)
        return hashed, salt
    
    @classmethod
    def verify_with_salt(cls, data: str, hashed: str, salt: str) -> bool:
        """
        Verify data against hash with salt
        
        Args:
            data: Data to verify
            hashed: Stored hash
            salt: Stored salt
        
        Returns:
            True if matches
        """
        salted_data = data + salt
        computed_hash = cls.sha256(salted_data)
        return hmac.compare_digest(computed_hash, hashed)
    
    @classmethod
    def generate_webhook_signature(cls, secret: str, payload: str) -> str:
        """Generate webhook signature for payload verification"""
        return cls.hmac_sha256(secret, payload)
    
    @classmethod
    def verify_webhook_signature(cls, secret: str, payload: str, signature: str) -> bool:
        """Verify webhook signature"""
        expected = cls.hmac_sha256(secret, payload)
        return hmac.compare_digest(expected, signature)
