"""
API Key Authentication - SHA-256 Hashed Key Validation
Secure key storage with hash-only database
Version: 31.0
"""

import hashlib
import secrets
from typing import Tuple, Optional
from datetime import datetime
import logging

from core.supabase_client import supabase

logger = logging.getLogger(__name__)


class APIKeyManager:
    """Manage API keys for developers and enterprises"""
    
    @staticmethod
    def generate_key() -> Tuple[str, str]:
        """
        Generate a new API key and its hash
        
        Returns:
            Tuple of (raw_key, hashed_key)
        """
        # Generate high-entropy key
        raw_key = f"sk_sov_{secrets.token_urlsafe(32)}"
        
        # SHA-256 hash for storage
        hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
        
        return raw_key, hashed_key
    
    @staticmethod
    async def create_key(
        developer_id: str,
        name: str,
        initial_balance_usd: float = 10.0
    ) -> Optional[str]:
        """
        Create a new API key for a developer
        
        Args:
            developer_id: Developer identifier
            name: Human-readable key name
            initial_balance_usd: Initial credit balance
        
        Returns:
            Raw API key (show once) or None if failed
        """
        raw_key, hashed_key = APIKeyManager.generate_key()
        
        try:
            supabase.table("developer_api_keys").insert({
                "api_key_hash": hashed_key,
                "developer_id": developer_id,
                "key_name": name,
                "account_balance_usd": initial_balance_usd,
                "is_active": True,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            logger.info(f"Created API key for {developer_id}: {name}")
            return raw_key
            
        except Exception as e:
            logger.error(f"Failed to create API key: {e}")
            return None
    
    @staticmethod
    async def validate_key(raw_key: str) -> Tuple[bool, Optional[dict]]:
        """
        Validate an API key
        
        Args:
            raw_key: Raw API key string
        
        Returns:
            Tuple of (is_valid, key_data)
        """
        if not raw_key or not raw_key.startswith("sk_sov_"):
            return False, None
        
        hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
        
        try:
            result = supabase.table("developer_api_keys").select("*").eq("api_key_hash", hashed_key).execute()
            
            if not result.data:
                return False, None
            
            key_data = result.data[0]
            
            if not key_data.get("is_active", False):
                return False, None
            
            if key_data.get("account_balance_usd", 0) <= 0:
                return False, None
            
            return True, key_data
            
        except Exception as e:
            logger.error(f"Key validation error: {e}")
            return False, None
    
    @staticmethod
    async def deduct_credits(raw_key: str, amount_usd: float) -> bool:
        """
        Deduct credits from an API key
        
        Args:
            raw_key: Raw API key
            amount_usd: Amount to deduct
        
        Returns:
            True if successful, False otherwise
        """
        hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
        
        try:
            result = supabase.table("developer_api_keys").select("account_balance_usd").eq("api_key_hash", hashed_key).execute()
            
            if not result.data:
                return False
            
            current_balance = float(result.data[0]["account_balance_usd"])
            
            if current_balance < amount_usd:
                return False
            
            new_balance = current_balance - amount_usd
            
            supabase.table("developer_api_keys").update({
                "account_balance_usd": new_balance,
                "last_used_at": datetime.utcnow().isoformat()
            }).eq("api_key_hash", hashed_key).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Credit deduction failed: {e}")
            return False
    
    @staticmethod
    async def revoke_key(hashed_key: str) -> bool:
        """Revoke an API key"""
        try:
            supabase.table("developer_api_keys").update({
                "is_active": False,
                "revoked_at": datetime.utcnow().isoformat()
            }).eq("api_key_hash", hashed_key).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Key revocation failed: {e}")
            return False
