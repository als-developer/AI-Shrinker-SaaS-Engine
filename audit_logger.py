"""
Audit Logger - Immutable Compliance Audit Trail
Complete logging for security and regulatory compliance
Version: 31.0
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from core.supabase_client import supabase
from core.redis_client import redis_client

logger = logging.getLogger(__name__)


class AuditLogger:
    """Immutable audit logging for compliance"""
    
    @classmethod
    async def log(
        cls,
        action: str,
        user_id: str,
        resource: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """
        Log an audit event
        
        Args:
            action: Action performed (create, read, update, delete, authenticate)
            user_id: User who performed action
            resource: Resource affected (api_key, organization, wallet, etc.)
            details: Additional details about the action
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Audit log ID
        """
        audit_id = f"audit_{datetime.utcnow().timestamp()}_{user_id[:8]}"
        
        audit_entry = {
            "audit_id": audit_id,
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user_id": user_id,
            "resource": resource,
            "details": details,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "environment": os.getenv("ENVIRONMENT", "production")
        }
        
        # Store in database
        try:
            await supabase.table_insert("audit_logs", audit_entry)
            
            # Also cache recent logs in Redis for quick access
            await redis_client.lpush("recent_audit_logs", json.dumps(audit_entry))
            await redis_client.ltrim("recent_audit_logs", 0, 999)
            
            logger.info(f"Audit log created: {audit_id} - {action}")
            
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
            # Fallback to file logging
            with open("audit_fallback.log", "a") as f:
                f.write(json.dumps(audit_entry) + "\n")
        
        return audit_id
    
    @classmethod
    async def log_api_call(
        cls,
        user_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        latency_ms: float,
        api_key_hash: Optional[str] = None
    ) -> str:
        """Log API call for analytics and security"""
        return await cls.log(
            action="api_call",
            user_id=user_id,
            resource=endpoint,
            details={
                "method": method,
                "status_code": status_code,
                "latency_ms": latency_ms,
                "api_key_hash": api_key_hash[:16] if api_key_hash else None
            }
        )
    
    @classmethod
    async def log_security_event(
        cls,
        event_type: str,
        user_id: str,
        severity: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None
    ) -> str:
        """Log security-related events"""
        details["severity"] = severity
        return await cls.log(
            action=f"security_{event_type}",
            user_id=user_id,
            resource="security",
            details=details,
            ip_address=ip_address
        )
    
    @classmethod
    async def get_user_audit_trail(cls, user_id: str, limit: int = 100) -> list:
        """Get audit trail for a specific user"""
        try:
            logs = await supabase.table_select(
                "audit_logs",
                {"user_id": user_id}
            )
            return sorted(logs, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]
        except Exception as e:
            logger.error(f"Failed to get audit trail: {e}")
            return []
    
    @classmethod
    async def get_resource_audit(cls, resource: str, resource_id: str, limit: int = 100) -> list:
        """Get audit trail for a specific resource"""
        try:
            # This requires a more complex query in production
            # Simplified for now
            logs = await supabase.table_select("audit_logs")
            filtered = [
                log for log in logs 
                if log.get("resource") == resource and resource_id in str(log.get("details", {}))
            ]
            return sorted(filtered, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]
        except Exception as e:
            logger.error(f"Failed to get resource audit: {e}")
            return []


import os
