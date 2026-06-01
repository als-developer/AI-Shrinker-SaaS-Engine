"""
Security Event Logger - Immutable Security Audit Trail
For compliance and security incident investigation
Version: 31.0
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import logging

from core.supabase_client import supabase
from core.redis_client import redis_client

logger = logging.getLogger(__name__)


class SecurityEventType(str, Enum):
    """Security event types for classification"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    MFA_VERIFIED = "mfa_verified"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    API_KEY_USED = "api_key_used"
    PERMISSION_CHANGE = "permission_change"
    ROLE_CHANGE = "role_change"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_BREACH = "rate_limit_breach"
    SLA_VIOLATION = "sla_violation"
    DATA_EXPORT = "data_export"
    DATA_DELETION = "data_deletion"


class SecurityEventLogger:
    """Immutable security event logging"""
    
    @classmethod
    async def log_event(
        cls,
        event_type: SecurityEventType,
        user_id: Optional[str],
        severity: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """
        Log a security event
        
        Args:
            event_type: Type of security event
            user_id: Affected user (if any)
            severity: Critical, high, medium, low, info
            details: Event details
            ip_address: Source IP address
            user_agent: Client user agent
        
        Returns:
            Event ID
        """
        event_id = f"sec_{datetime.utcnow().timestamp()}_{user_id or 'system'}"
        
        event_data = {
            "event_id": event_id,
            "event_type": event_type.value,
            "user_id": user_id,
            "severity": severity,
            "details": details,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Store in database
            await supabase.table_insert("security_events", event_data)
            
            # Also store in Redis for recent events
            await redis_client.lpush("recent_security_events", json.dumps(event_data))
            await redis_client.ltrim("recent_security_events", 0, 999)
            
            # Log critical events to console/alert
            if severity in ["critical", "high"]:
                logger.warning(f"SECURITY ALERT: {event_type.value} - {details}")
                # Send to Slack/PagerDuty for critical events
                from services.slack_alerter import SlackAlerter
                await SlackAlerter.send_security_alert(event_type.value, details)
            
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
            return None
    
    @classmethod
    async def log_login(cls, email: str, success: bool, ip: str, user_agent: str) -> str:
        """Log login attempt"""
        event_type = SecurityEventType.LOGIN_SUCCESS if success else SecurityEventType.LOGIN_FAILED
        severity = "info" if success else "warning"
        
        return await cls.log_event(
            event_type=event_type,
            user_id=email,
            severity=severity,
            details={"email": email, "success": success},
            ip_address=ip,
            user_agent=user_agent
        )
    
    @classmethod
    async def log_api_key_event(cls, user_id: str, action: str, key_name: str, success: bool) -> str:
        """Log API key creation or revocation"""
        event_type = SecurityEventType.API_KEY_CREATED if action == "created" else SecurityEventType.API_KEY_REVOKED
        severity = "info"
        
        return await cls.log_event(
            event_type=event_type,
            user_id=user_id,
            severity=severity,
            details={"key_name": key_name, "action": action, "success": success}
        )
    
    @classmethod
    async def log_suspicious_activity(cls, user_id: str, activity: str, details: Dict) -> str:
        """Log suspicious activity for investigation"""
        return await cls.log_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            user_id=user_id,
            severity="high",
            details={"activity": activity, **details}
        )
