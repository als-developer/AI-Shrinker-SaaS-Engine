"""
Slack Alert Integration - Real-time Alert Notifications
For sending alerts to Slack channels
Version: 31.0
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
import logging

logger = logging.getLogger(__name__)


class SlackAlertManager:
    """Send alerts and notifications to Slack"""
    
    WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
    
    @classmethod
    async def send_alert(
        cls,
        title: str,
        message: str,
        severity: str = "warning",
        fields: List[Dict] = None,
        color: str = None
    ) -> bool:
        """
        Send alert to Slack
        
        Args:
            title: Alert title
            message: Alert message
            severity: severity (info, warning, error, critical)
            fields: Additional fields to display
            color: Custom color override
        
        Returns:
            True if sent successfully
        """
        if not cls.WEBHOOK_URL:
            logger.warning("Slack webhook not configured")
            return False
        
        color_map = {
            "info": "#36a64f",
            "warning": "#f2c744",
            "error": "#e74c3c",
            "critical": "#9b59b6"
        }
        
        final_color = color or color_map.get(severity, "#cccccc")
        
        payload = {
            "attachments": [{
                "color": final_color,
                "title": f"[{severity.upper()}] {title}",
                "text": message,
                "fields": fields or [],
                "footer": "Sovereign Grid Alert System",
                "ts": int(datetime.utcnow().timestamp())
            }]
        }
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(cls.WEBHOOK_URL, json=payload)
                
                if response.status_code == 200:
                    logger.info(f"Slack alert sent: {title}")
                    return True
                else:
                    logger.error(f"Slack alert failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False
    
    @classmethod
    async def send_deployment_alert(cls, version: str, status: str, commits: List[str]) -> bool:
        """Send deployment notification"""
        fields = [
            {"title": "Version", "value": version, "short": True},
            {"title": "Status", "value": status, "short": True},
            {"title": "Commits", "value": "\n".join(commits[:5]), "short": False}
        ]
        
        color = "good" if status == "success" else "danger"
        return await cls.send_alert(
            title=f"Deployment {status}",
            message=f"Version {version} has been deployed",
            severity="info",
            fields=fields,
            color=color
        )
    
    @classmethod
    async def send_performance_alert(cls, metric: str, value: float, threshold: float) -> bool:
        """Send performance threshold alert"""
        fields = [
            {"title": "Metric", "value": metric, "short": True},
            {"title": "Current Value", "value": str(value), "short": True},
            {"title": "Threshold", "value": str(threshold), "short": True},
            {"title": "Action Required", "value": "Investigate immediately", "short": False}
        ]
        
        return await cls.send_alert(
            title=f"Performance Alert: {metric}",
            message=f"Performance metric exceeded threshold",
            severity="warning",
            fields=fields
        )
    
    @classmethod
    async def send_sla_alert(cls, org_id: str, uptime: float, guarantee: float) -> bool:
        """Send SLA violation alert"""
        fields = [
            {"title": "Organization", "value": org_id, "short": True},
            {"title": "Current Uptime", "value": f"{uptime}%", "short": True},
            {"title": "SLA Guarantee", "value": f"{guarantee}%", "short": True},
            {"title": "Action", "value": "Refund processing initiated", "short": False}
        ]
        
        return await cls.send_alert(
            title=f"SLA Violation: {org_id}",
            message=f"Uptime fell below guarantee",
            severity="error",
            fields=fields
        )
    
    @classmethod
    async def send_security_alert(cls, event_type: str, user_id: str, details: Dict) -> bool:
        """Send security event alert"""
        fields = [
            {"title": "Event Type", "value": event_type, "short": True},
            {"title": "User", "value": user_id, "short": True},
            {"title": "Details", "value": json.dumps(details, indent=2), "short": False}
        ]
        
        return await cls.send_alert(
            title=f"Security Alert: {event_type}",
            message=f"Security event detected for user {user_id}",
            severity="critical",
            fields=fields
        )
