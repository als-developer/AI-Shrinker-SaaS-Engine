"""
Key Deactivator - Emergency API Key Suspension
Instant key revocation for security incidents
Version: 31.0
"""

import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from core.supabase_client import supabase
from core.redis_client import redis_client

logger = logging.getLogger(__name__)


class KeyDeactivator:
    """Emergency API key deactivation service"""
    
    @classmethod
    async def deactivate_key(cls, api_key: str, reason: str = "security_incident") -> Dict[str, Any]:
        """
        Immediately deactivate an API key
        
        Args:
            api_key: API key to deactivate
            reason: Reason for deactivation
            
        Returns:
            Deactivation result
        """
        hashed_key = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Find the key
        key_record = await supabase.table_select(
            "developer_api_keys",
            {"api_key_hash": hashed_key}
        )
        
        if not key_record:
            return {"error": "API key not found", "success": False}
        
        key_data = key_record[0]
        
        # Deactivate
        await supabase.table_update(
            "developer_api_keys",
            {
                "is_active": False,
                "deactivated_at": datetime.utcnow().isoformat(),
                "deactivation_reason": reason
            },
            {"api_key_hash": hashed_key}
        )
        
        # Add to revocation list in Redis for instant blocking
        await redis_client.setex(
            f"revoked_key:{hashed_key}",
            86400 * 30,  # 30 days
            json.dumps({
                "deactivated_at": datetime.utcnow().isoformat(),
                "reason": reason
            })
        )
        
        logger.warning(f"API key deactivated for {key_data['developer_id']}: {reason}")
        
        # Notify developer
        await cls._notify_deactivation(key_data["developer_id"], reason)
        
        return {
            "success": True,
            "developer_id": key_data["developer_id"],
            "deactivated_at": datetime.utcnow().isoformat(),
            "reason": reason
        }
    
    @classmethod
    async def deactivate_all_for_developer(cls, developer_id: str, reason: str) -> Dict[str, Any]:
        """Deactivate all API keys for a developer"""
        keys = await supabase.table_select(
            "developer_api_keys",
            {"developer_id": developer_id, "is_active": True}
        )
        
        deactivated_count = 0
        for key in keys:
            result = await cls.deactivate_key_by_hash(key["api_key_hash"], reason)
            if result.get("success"):
                deactivated_count += 1
        
        return {
            "success": True,
            "developer_id": developer_id,
            "deactivated_count": deactivated_count,
            "reason": reason
        }
    
    @classmethod
    async def deactivate_key_by_hash(cls, key_hash: str, reason: str) -> Dict[str, Any]:
        """Deactivate key by its hash"""
        await supabase.table_update(
            "developer_api_keys",
            {
                "is_active": False,
                "deactivated_at": datetime.utcnow().isoformat(),
                "deactivation_reason": reason
            },
            {"api_key_hash": key_hash}
        )
        
        await redis_client.setex(f"revoked_key:{key_hash}", 86400 * 30, reason)
        
        return {"success": True, "key_hash": key_hash}
    
    @classmethod
    async def is_revoked(cls, api_key_hash: str) -> bool:
        """Check if a key is revoked"""
        revoked = await redis_client.get(f"revoked_key:{api_key_hash}")
        return revoked is not None
    
    @classmethod
    async def _notify_deactivation(cls, developer_id: str, reason: str):
        """Notify developer about key deactivation"""
        # In production, send email/Slack notification
        logger.info(f"Notifying {developer_id} about key deactivation: {reason}")
