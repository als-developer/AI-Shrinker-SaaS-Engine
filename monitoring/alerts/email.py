
"""
Email Alert Integration - Send Alerts via Email
For critical alerts requiring email notification
Version: 31.0
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from services.email_sender import EmailSender

logger = logging.getLogger(__name__)


class EmailAlertManager:
    """Send alerts via email for critical issues"""
    
    # Default recipients for different severity levels
    RECIPIENTS = {
        "critical": os.getenv("ALERT_EMAIL_CRITICAL", "oncall@sovereigngrid.com").split(","),
        "error": os.getenv("ALERT_EMAIL_ERROR", "team@sovereigngrid.com").split(","),
        "warning": os.getenv("ALERT_EMAIL_WARNING", "ops@sovereigngrid.com").split(","),
        "info": os.getenv("ALERT_EMAIL_INFO", "alerts@sovereigngrid.com").split(",")
    }
    
    @classmethod
    async def send_alert(
        cls,
        title: str,
        message: str,
        severity: str = "warning",
        details: Dict = None
    ) -> bool:
        """
        Send email alert
        
        Args:
            title: Alert title
            message: Alert message
            severity: severity (info, warning, error, critical)
            details: Additional details to include
        
        Returns:
            True if sent successfully
        """
        recipients = cls.RECIPIENTS.get(severity, cls.RECIPIENTS["warning"])
        
        # Build HTML email
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .alert {{
                    border-left: 4px solid #e74c3c;
                    padding: 15px;
                    margin: 20px 0;
                    background: #fef5f5;
                }}
                .critical {{ border-left-color: #9b59b6; }}
                .error {{ border-left-color: #e74c3c; }}
                .warning {{ border-left-color: #f2c744; }}
                .info {{ border-left-color: #36a64f; }}
                .details {{
                    background: #f4f4f4;
                    padding: 10px;
                    font-family: monospace;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="alert {severity}">
                <h2>[{severity.upper()}] {title}</h2>
                <p>{message}</p>
                <p><strong>Time:</strong> {datetime.utcnow().isoformat()}</p>
        """
        
        if details:
            html += """
                <div class="details">
                    <strong>Details:</strong><br>
                    <pre>{}</pre>
                </div>
            """.format(json.dumps(details, indent=2))
        
        html += """
                <hr>
                <p style="font-size: 12px; color: #999;">
                    This is an automated alert from Sovereign Grid Monitoring System.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Send to all recipients
        success = True
        for recipient in recipients:
            result = await EmailSender.send_email(
                to_email=recipient.strip(),
                subject=f"[{severity.upper()}] Sovereign Grid Alert: {title}",
                html_content=html
            )
            if not result:
                success = False
                logger.error(f"Failed to send email alert to {recipient}")
        
        return success
    
    @classmethod
    async def send_critical_alert(cls, title: str, message: str, details: Dict = None) -> bool:
        """Send critical alert (highest priority)"""
        return await cls.send_alert(title, message, "critical", details)
    
    @classmethod
    async def send_system_down_alert(cls, service: str, error: str) -> bool:
        """Send system down alert"""
        return await cls.send_critical_alert(
            title=f"Service Down: {service}",
            message=f"The {service} service is currently unavailable.",
            details={"service": service, "error": error, "timestamp": datetime.utcnow().isoformat()}
        )
    
    @classmethod
    async def send_daily_report(cls, metrics: Dict) -> bool:
        """Send daily health report"""
        html = f"""
        <h2>Daily Health Report - {datetime.utcnow().date()}</h2>
        <table border="1" cellpadding="10">
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total API Calls</td><td>{metrics.get('total_api_calls', 0)}</td></tr>
            <tr><td>Active Users</td><td>{metrics.get('active_users', 0)}</td></tr>
            <tr><td>Error Rate</td><td>{metrics.get('error_rate', 0)}%</td></tr>
            <tr><td>Avg Response Time</td><td>{metrics.get('avg_response_ms', 0)}ms</td></tr>
            <tr><td>Uptime</td><td>{metrics.get('uptime', 100)}%</td></tr>
        </table>
        """
        
        return await EmailSender.send_email(
            to_email="team@sovereigngrid.com",
            subject=f"Daily Health Report - {datetime.utcnow().date()}",
            html_content=html
        )


import json
