"""
JWT Token Module - Secure Token Generation and Validation
For API authentication and session management
Version: 31.0
"""

import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import os
import logging

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-jwt-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_SECONDS = 3600  # 1 hour


class JWTManager:
    """JWT token management for authentication"""
    
    @classmethod
    def create_token(cls, payload: Dict[str, Any], expiry_seconds: int = JWT_EXPIRY_SECONDS) -> str:
        """
        Create a JWT token
        
        Args:
            payload: Token payload data
            expiry_seconds: Token expiry in seconds
        
        Returns:
            Encoded JWT token
        """
        payload_copy = payload.copy()
        payload_copy["exp"] = datetime.utcnow() + timedelta(seconds=expiry_seconds)
        payload_copy["iat"] = datetime.utcnow()
        
        token = jwt.encode(payload_copy, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token
    
    @classmethod
    def verify_token(cls, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token to verify
        
        Returns:
            Tuple of (is_valid, payload)
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return True, payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return False, None
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return False, None
    
    @classmethod
    def create_user_token(cls, user_id: str, email: str, role: str = "user") -> str:
        """Create a user authentication token"""
        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "type": "access"
        }
        return cls.create_token(payload)
    
    @classmethod
    def create_refresh_token(cls, user_id: str) -> str:
        """Create a refresh token (longer expiry)"""
        payload = {
            "sub": user_id,
            "type": "refresh"
        }
        return cls.create_token(payload, expiry_seconds=JWT_EXPIRY_SECONDS * 24 * 7)  # 7 days
    
    @classmethod
    def create_api_token(cls, developer_id: str, key_name: str) -> str:
        """Create an API token for developers"""
        payload = {
            "sub": developer_id,
            "key_name": key_name,
            "type": "api",
            "scope": ["read", "write"]
        }
        return cls.create_token(payload, expiry_seconds=JWT_EXPIRY_SECONDS * 30)  # 30 days
    
    @classmethod
    def get_user_from_token(cls, token: str) -> Optional[str]:
        """Extract user ID from token"""
        is_valid, payload = cls.verify_token(token)
        if is_valid and payload:
            return payload.get("sub")
        return None
