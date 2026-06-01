"""
Auth Guard - JWT Token Validation & Session Management
Supabase Auth integration with row-level security
Version: 31.0
"""

import os
import jwt
from typing import Dict, Optional
from fastapi import HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from core.supabase_client import supabase

logger = logging.getLogger(__name__)

# Security configuration
security_bearer = HTTPBearer(auto_error=False)

# JWT secret from environment
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")


async def authenticate_user(
    authorization: Optional[str] = Header(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
) -> Dict[str, str]:
    """
    Authenticate user via JWT token
    
    Args:
        authorization: Bearer token header
        credentials: FastAPI security credentials
    
    Returns:
        Dict with user_id and email
    
    Raises:
        HTTPException 401 if authentication fails
    """
    token = None
    
    # Extract token from either source
    if credentials:
        token = credentials.credentials
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Decode and verify JWT
        decoded = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False}
        )
        
        user_id = decoded.get("sub")
        email = decoded.get("email", "")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing subject")
        
        # Verify user exists in database
        try:
            profile = supabase.table("tenant_user_profiles").select("*").eq("id", user_id).execute()
            if not profile.data:
                # Create profile if it doesn't exist
                supabase.table("tenant_user_profiles").insert({
                    "id": user_id,
                    "user_id": user_id,
                    "email": email,
                    "created_at": "now()"
                }).execute()
        except Exception as e:
            logger.warning(f"Profile lookup failed: {e}")
        
        return {
            "user_id": user_id,
            "email": email,
            "authenticated": True
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


async def authenticate_developer(
    x_sovereign_key: Optional[str] = Header(None)
) -> str:
    """
    Authenticate developer via API key
    
    Args:
        x_sovereign_key: API key from header
    
    Returns:
        Developer ID
    
    Raises:
        HTTPException 401 if invalid key
    """
    if not x_sovereign_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-Sovereign-Key header"
        )
    
    # Simple validation - in production, verify against database
    if not x_sovereign_key.startswith("sk_sov_"):
        raise HTTPException(status_code=401, detail="Invalid API key format")
    
    # In production, verify against database and check balance
    # For now, return placeholder
    return "dev_authenticated"
