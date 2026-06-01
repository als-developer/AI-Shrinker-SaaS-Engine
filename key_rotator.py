"""
Key Rotator - Automated API Key Rotation & Management
Secure key lifecycle management with zero-downtime rotation
Version: 31.0
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import logging

from core.supabase_client import supabase
from core.redis_client import redis_client

logger = logging.getLogger(__name__)


class KeyRotator:
    """Automated API key rotation and lifecycle management"""
    
    @classmethod
    async def rotate_key(cls, old_key: str) -> Dict[str, Any]:
        """
        Rotate an API key to a new one
        
        Args:
            old_key: Existing API key to rotate
            
        Returns:
            New key information
        """
        # Validate old key
        hashed_old = hashlib.sha256(old_key.encode()).hexdigest()
        
        key_record = await supabase.table_select(
            "developer_api_keys",
            {"api_key_hash": hashed_old}
        )
        
        if not key_record:
            return {"error": "Invalid API key", "success": False}
        
        key_data = key_record[0]
        developer_id = key_data["developer_id"]
        
        # Deactivate old key
        await supabase.table_update(
            "developer_api_keys",
            {
                "is_active": False,
                "deactivated_at": datetime.utcnow().isoformat(),
                "deactivation_reason": "rotated"
            },
            {"api_key_hash": hashed_old}
        )
        
        # Create new key
        new_key = f"sk_sov_{secrets.token_urlsafe(32)}"
        new_hashed = hashlib.sha256(new_key.encode()).hexdigest()
        
        await supabase.table_insert("developer_api_keys", {
            "api_key_hash": new_hashed,
            "developer_id": developer_id,
            "key_name": f"{key_data.get('key_name', 'api_key')}_rotated_{datetime.utcnow().strftime('%Y%m%d')}",
            "account_balance_usd": key_data.get("account_balance_usd", 0),
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "previous_key_hash": hashed_old
        })
        
        # Cache old key for grace period
        await redis_client.setex(
            f"rotated_key:{hashed_old}",
            86400,  # 24 hour grace period
            new_hashed
        )
        
        logger.info(f"Rotated key for developer {developer_id}")
        
        return {
            "success": True,
            "new_key": new_key,
            "grace_period_seconds": 86400,
            "message": "Old key will continue to work for 24 hours"
        }
    
    @classmethod
    async def schedule_rotation(cls, developer_id: str, days_before: int = 30) -> bool:
        """Schedule key rotation for a developer"""
        rotation_id = f"rot_{developer_id}_{datetime.utcnow().timestamp()}"
        
        await supabase.table_insert("scheduled_rotations", {
            "rotation_id": rotation_id,
            "developer_id": developer_id,
            "scheduled_date": (datetime.utcnow() + timedelta(days=days_before)).isoformat(),
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Scheduled key rotation for {developer_id} in {days_before} days")
        return True
    
    @classmethod
    async def check_grace_period(cls, old_key_hash: str) -> Optional[str]:
        """Check if an old key is still valid during grace period"""
        new_key_hash = await redis_client.get(f"rotated_key:{old_key_hash}")
        return new_key_hash
