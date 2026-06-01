"""
Session Management - Secure User Session Handling
JWT-based sessions with refresh tokens and device tracking
Version: 31.0
"""

import uuid
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import os
import logging

from core.supabase_client import supabase
from core.redis_client import redis_client

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30


class SessionManager:
    """Secure session management with JWT tokens"""
    
    @classmethod
    def create_tokens(cls, user_id: str, device_info: Dict = None) -> Dict[str, str]:
        """
        Create access and refresh tokens for a user
        
        Args:
            user_id: User identifier
            device_info: Device information for tracking
        
        Returns:
            Dict with access_token and refresh_token
        """
        session_id = str(uuid.uuid4())
        
        # Access token (short-lived)
        access_payload = {
            "sub": user_id,
            "session_id": session_id,
            "type": "access",
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.utcnow()
        }
        access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        # Refresh token (long-lived)
        refresh_payload = {
            "sub": user_id,
            "session_id": session_id,
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            "iat": datetime.utcnow()
        }
        refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        # Store session in Redis
        session_data = {
            "user_id": user_id,
            "session_id": session_id,
            "device_info": device_info or {},
            "created_at": datetime.utcnow().isoformat(),
            "access_token": access_token
        }
        redis_client.setex(
            f"session:{session_id}",
            ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            json.dumps(session_data)
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    @classmethod
    def verify_access_token(cls, token: str) -> Tuple[bool, Optional[Dict]]:
        """
        Verify and decode access token
        
        Args:
            token: JWT access token
        
        Returns:
            Tuple of (is_valid, payload)
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            
            if payload.get("type") != "access":
                return False, None
            
            # Check if session is still valid in Redis
            session_id = payload.get("session_id")
            if session_id:
                session_data = redis_client.get(f"session:{session_id}")
                if not session_data:
                    return False, None
            
            return True, payload
            
        except jwt.ExpiredSignatureError:
            return False, None
        except jwt.InvalidTokenError:
            return False, None
    
    @classmethod
    def refresh_access_token(cls, refresh_token: str) -> Tuple[bool, Optional[Dict]]:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: JWT refresh token
        
        Returns:
            Tuple of (success, new_tokens)
        """
        try:
            payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            
            if payload.get("type") != "refresh":
                return False, None
            
            user_id = payload.get("sub")
            session_id = payload.get("session_id")
            
            if not user_id or not session_id:
                return False, None
            
            # Create new tokens
            new_tokens = cls.create_tokens(user_id)
            return True, new_tokens
            
        except jwt.ExpiredSignatureError:
            return False, None
        except jwt.InvalidTokenError:
            return False, None
    
    @classmethod
    async def revoke_session(cls, session_id: str) -> bool:
        """Revoke a user session"""
        try:
            redis_client.delete(f"session:{session_id}")
            
            # Also revoke in database for audit
            supabase.table("user_sessions").update({
                "revoked_at": datetime.utcnow().isoformat()
            }).eq("session_id", session_id).execute()
            
            logger.info(f"Session revoked: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke session: {e}")
            return False
    
    @classmethod
    async def revoke_all_sessions(cls, user_id: str) -> bool:
        """Revoke all sessions for a user"""
        try:
            # Find all sessions in Redis
            keys = redis_client.keys(f"session:*")
            for key in keys:
                session_data = redis_client.get(key)
                if session_data:
                    data = json.loads(session_data)
                    if data.get("user_id") == user_id:
                        redis_client.delete(key)
            
            # Revoke in database
            supabase.table("user_sessions").update({
                "revoked_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).execute()
            
            logger.info(f"All sessions revoked for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke all sessions: {e}")
            return False
