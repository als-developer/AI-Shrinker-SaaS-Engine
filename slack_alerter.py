"""
Slack Alerter - Real-Time Slack Notifications
System alerts, security events, and team notifications
Version: 31.0
"""

import os
import json
from typing import Dict, Any, List, Optional
import httpx
import logging

logger = logging.getLogger(__name__)


class SlackAlerter:
    """Send alerts and notifications to Slack channels"""
    
    WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
    ALERT_CHANNEL = os.getenv("SLACK_ALERT_CHANNEL", "#alerts")
    
    @classmethod
    async def send_alert(cls, title: str, message: str, severity: str = "warning") -> bool:
        """
        Send an alert to Slack
        
        Args:
            title: Alert title
            message: Alert message
            severity: severity (info, warning, error, critical)
            
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
        
        payload = {
            "channel": cls.ALERT_CHANNEL,
            "attachments": [{
                "color": color_map.get(severity, "#cccccc"),
                "title": f"[{severity.upper()}] {title}",
                "text": message,
                "fields": [
                    {"title": "Time", "value": str(datetime.utcnow()), "short": True},
                    {"title": "Environment", "value": os.getenv("ENVIRONMENT", "production"), "short": True}
                ],
                "footer": "Sovereign Grid Alert System"
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
    async def send_security_alert(cls, event_type: str, details: Dict) -> bool:
        """Send security event alert"""
        message = f"**Event:** {event_type}\n**Details:** ```{json.dumps(details, indent=2)}```"
        return await cls.send_alert(f"Security: {event_type}", message, "critical")
    
    @classmethod
    async def send_deployment_alert(cls, version: str, status: str, commits: List[str]) -> bool:
        """Send deployment notification"""
        message = f"**Version:** {version}\n**Status:** {status}\n**Commits:**\n" + "\n".join(f"- {c}" for c in commits[:5])
        return await cls.send_alert(f"Deployment {status}", message, "info")
    
    @classmethod
    async def send_performance_alert(cls, metric: str, value: float, threshold: float) -> bool:
        """Send performance threshold alert"""
        message = f"**Metric:** {metric}\n**Current Value:** {value}\n**Threshold:** {threshold}\n**Action Required:** Investigate immediately."
        return await cls.send_alert(f"Performance Alert: {metric}", message, "warning")
    
    @classmethod
    async def send_sla_alert(cls, org_id: str, uptime: float, guarantee: float) -> bool:
        """Send SLA violation alert"""
        message = f"**Organization:** {org_id}\n**Current Uptime:** {uptime}%\n**SLA Guarantee:** {guarantee}%\n**Action:** Refund processing initiated."
        return await cls.send_alert(f"SLA Violation: {org_id}", message, "error")


from datetime import datetime
