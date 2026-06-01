"""
Email Sender - Async Email Delivery Service
Handles transactional emails for onboarding, alerts, and notifications
Version: 31.0
"""

import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)


class EmailSender:
    """Async email delivery service"""
    
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@sovereigngrid.com")
    FROM_NAME = os.getenv("FROM_NAME", "Sovereign Grid Systems")
    
    _email_queue = asyncio.Queue()
    _worker_task = None
    
    @classmethod
    async def start_worker(cls):
        """Start email worker"""
        if cls._worker_task is None:
            cls._worker_task = asyncio.create_task(cls._process_queue())
            logger.info("Email worker started")
    
    @classmethod
    async def send_email(
        cls,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> str:
        """
        Queue email for sending
        
        Returns:
            Email ID
        """
        email_id = f"email_{datetime.utcnow().timestamp()}_{to_email[:8]}"
        
        email_data = {
            "id": email_id,
            "to": to_email,
            "subject": subject,
            "html": html_content,
            "text": text_content or cls._html_to_text(html_content),
            "created_at": datetime.utcnow().isoformat(),
            "attempts": 0
        }
        
        await cls._email_queue.put(email_data)
        await cls.start_worker()
        
        logger.info(f"Email queued: {email_id} to {to_email}")
        return email_id
    
    @classmethod
    async def send_welcome_email(cls, to_email: str, name: str, api_key: str) -> str:
        """Send welcome email to new developer"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
            .key {{ background: #f4f4f4; padding: 15px; font-family: monospace; border-radius: 5px; word-break: break-all; }}
            .button {{ background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; }}
            .footer {{ font-size: 12px; color: #999; text-align: center; margin-top: 30px; }}
        </style></head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚡ Welcome to Sovereign Grid</h1>
                </div>
                <div style="padding: 30px;">
                    <h2>Hello {name},</h2>
                    <p>Your enterprise developer account has been successfully created!</p>
                    
                    <h3>🔑 Your API Key</h3>
                    <div class="key">{api_key}</div>
                    <p><strong>⚠️ Important:</strong> Save this key immediately. It will not be shown again.</p>
                    
                    <h3>🚀 Quick Start</h3>
                    <a href="https://sovereigngrid.com/api/docs" class="button">View API Documentation</a>
                    
                    <h3>💰 Account Balance</h3>
                    <p>Your account has been pre-funded with <strong>$10.00 USD</strong> in credits.</p>
                </div>
                <div class="footer">
                    <p>© 2026 Sovereign Grid Systems. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await cls.send_email(to_email, f"Welcome to Sovereign Grid, {name}!", html)
    
    @classmethod
    async def send_invoice_email(cls, to_email: str, company_name: str, invoice_id: str, amount_usd: float) -> str:
        """Send invoice notification email"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><style>
            body {{ font-family: Arial, sans-serif; }}
            .invoice {{ border: 1px solid #ddd; padding: 20px; max-width: 600px; margin: 0 auto; }}
            .header {{ background: #2c3e50; color: white; padding: 15px; text-align: center; }}
            .amount {{ font-size: 24px; font-weight: bold; color: #27ae60; }}
        </style></head>
        <body>
            <div class="invoice">
                <div class="header">
                    <h2>Invoice {invoice_id}</h2>
                </div>
                <div style="padding: 20px;">
                    <p>Dear {company_name},</p>
                    <p>Your invoice for <strong>{amount_usd} USD</strong> is ready.</p>
                    <p class="amount">Amount Due: ${amount_usd}</p>
                    <p>Due Date: 30 days from invoice date</p>
                    <p><a href="https://sovereigngrid.com/billing">View and Pay Invoice</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await cls.send_email(to_email, f"Invoice {invoice_id} from Sovereign Grid", html)
    
    @classmethod
    async def send_alert_email(cls, to_email: str, alert_type: str, message: str) -> str:
        """Send system alert email"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><style>
            .alert {{ border-left: 4px solid #e74c3c; padding: 15px; background: #fef5f5; }}
        </style></head>
        <body>
            <div class="alert">
                <h3>🚨 System Alert: {alert_type}</h3>
                <p>{message}</p>
                <p>Time: {datetime.utcnow().isoformat()}</p>
            </div>
        </body>
        </html>
        """
        
        return await cls.send_email(to_email, f"[Alert] {alert_type}", html)
    
    @classmethod
    async def _process_queue(cls):
        """Process email queue"""
        while True:
            try:
                email = await cls._email_queue.get()
                await cls._send_single_email(email)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Email worker error: {e}")
                await asyncio.sleep(1)
    
    @classmethod
    async def _send_single_email(cls, email: Dict):
        """Send a single email with retry"""
        email_id = email["id"]
        
        for attempt in range(3):
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = email["subject"]
                msg["From"] = f"{cls.FROM_NAME} <{cls.FROM_EMAIL}>"
                msg["To"] = email["to"]
                
                # Attach parts
                part_text = MIMEText(email["text"], "plain")
                part_html = MIMEText(email["html"], "html")
                msg.attach(part_text)
                msg.attach(part_html)
                
                # Send
                async with aiosmtplib.SMTP(hostname=cls.SMTP_HOST, port=cls.SMTP_PORT) as smtp:
                    await smtp.starttls()
                    await smtp.login(cls.SMTP_USER, cls.SMTP_PASSWORD)
                    await smtp.send_message(msg)
                
                logger.info(f"Email sent: {email_id}")
                return
                
            except Exception as e:
                logger.warning(f"Email attempt {attempt + 1} failed for {email_id}: {e}")
                await asyncio.sleep(2 ** attempt)
        
        logger.error(f"Email failed after 3 attempts: {email_id}")
    
    @classmethod
    def _html_to_text(cls, html: str) -> str:
        """Convert HTML to plain text"""
        import re
        text = re.sub(r'<[^>]+>', '', html)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
