"""
Webhook Dispatcher - Asynchronous Webhook Delivery System
Reliable event-driven webhook notifications with retry logic
Version: 31.0
"""

import asyncio
import json
import hmac
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
import logging

from core.supabase_client import supabase
from core.redis_client import redis_client

logger = logging.getLogger(__name__)


class WebhookDispatcher:
    """Handle async webhook delivery with retry and signature verification"""
    
    # Queue for pending webhooks
    _webhook_queue = asyncio.Queue()
    _worker_task = None
    
    # Retry configuration
    MAX_RETRIES = 5
    RETRY_DELAYS = [1, 2, 4, 8, 16]  # seconds
    
    @classmethod
    async def start_worker(cls):
        """Start the background webhook worker"""
        if cls._worker_task is None or cls._worker_task.done():
            cls._worker_task = asyncio.create_task(cls._process_webhooks())
            logger.info("Webhook dispatcher worker started")
    
    @classmethod
    async def dispatch(
        cls,
        event_type: str,
        payload: Dict[str, Any],
        merchant_id: str,
        webhook_url: Optional[str] = None
    ) -> str:
        """
        Dispatch a webhook event
        
        Args:
            event_type: Type of event (payment.success, job.completed, etc.)
            payload: Event payload
            merchant_id: Merchant identifier
            webhook_url: Optional override URL
        
        Returns:
            Webhook ID
        """
        # Get webhook configuration
        if not webhook_url:
            config = await cls._get_webhook_config(merchant_id)
            if not config or not config.get("is_active"):
                logger.info(f"No active webhook for merchant {merchant_id}")
                return None
            webhook_url = config["webhook_url"]
        
        webhook_id = f"wh_{datetime.utcnow().timestamp()}_{merchant_id[:8]}"
        
        webhook_data = {
            "id": webhook_id,
            "merchant_id": merchant_id,
            "event_type": event_type,
            "payload": payload,
            "webhook_url": webhook_url,
            "attempts": 0,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Add to queue
        await cls._webhook_queue.put(webhook_data)
        
        # Ensure worker is running
        await cls.start_worker()
        
        return webhook_id
    
    @classmethod
    async def _process_webhooks(cls):
        """Background worker to process webhook queue"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            while True:
                try:
                    webhook = await cls._webhook_queue.get()
                    await cls._send_webhook(client, webhook)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Webhook processing error: {e}")
                    await asyncio.sleep(1)
    
    @classmethod
    async def _send_webhook(cls, client: httpx.AsyncClient, webhook: Dict):
        """Send webhook with retry logic"""
        webhook_id = webhook["id"]
        url = webhook["webhook_url"]
        
        # Prepare payload with signature
        payload = {
            "event": webhook["event_type"],
            "timestamp": datetime.utcnow().isoformat(),
            "data": webhook["payload"]
        }
        
        # Get secret for signature
        secret = await cls._get_merchant_secret(webhook["merchant_id"])
        
        # Generate signature
        if secret:
            signature = hmac.new(
                secret.encode(),
                json.dumps(payload, sort_keys=True).encode(),
                hashlib.sha256
            ).hexdigest()
            headers = {
                "X-Webhook-Signature": signature,
                "X-Webhook-Id": webhook_id
            }
        else:
            headers = {"X-Webhook-Id": webhook_id}
        
        headers["Content-Type"] = "application/json"
        
        for attempt in range(cls.MAX_RETRIES):
            try:
                response = await client.post(url, json=payload, headers=headers)
                
                if 200 <= response.status_code < 300:
                    # Success
                    await cls._log_result(webhook_id, "delivered", attempt + 1)
                    logger.info(f"Webhook {webhook_id} delivered successfully")
                    return
                else:
                    logger.warning(f"Webhook {webhook_id} returned {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"Webhook {webhook_id} attempt {attempt + 1} failed: {e}")
            
            # Retry with delay
            if attempt < cls.MAX_RETRIES - 1:
                await asyncio.sleep(cls.RETRY_DELAYS[attempt])
        
        # All retries failed
        await cls._log_result(webhook_id, "failed", cls.MAX_RETRIES)
        logger.error(f"Webhook {webhook_id} failed after {cls.MAX_RETRIES} attempts")
    
    @classmethod
    async def _get_webhook_config(cls, merchant_id: str) -> Optional[Dict]:
        """Get webhook configuration for merchant"""
        try:
            result = supabase.table("merchant_webhooks").select("*").eq("merchant_id", merchant_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get webhook config: {e}")
            return None
    
    @classmethod
    async def _get_merchant_secret(cls, merchant_id: str) -> Optional[str]:
        """Get merchant secret for signature generation"""
        try:
            result = supabase.table("merchant_accounts").select("webhook_secret").eq("merchant_id", merchant_id).execute()
            return result.data[0]["webhook_secret"] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get merchant secret: {e}")
            return None
    
    @classmethod
    async def _log_result(cls, webhook_id: str, status: str, attempts: int):
        """Log webhook delivery result"""
        try:
            supabase.table("webhook_delivery_logs").insert({
                "webhook_id": webhook_id,
                "status": status,
                "attempts": attempts,
                "completed_at": datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            logger.warning(f"Failed to log webhook result: {e}")
    
    @classmethod
    async def register_webhook(
        cls,
        merchant_id: str,
        webhook_url: str,
        events: List[str],
        secret: Optional[str] = None
    ) -> bool:
        """Register a new webhook endpoint"""
        try:
            supabase.table("merchant_webhooks").insert({
                "merchant_id": merchant_id,
                "webhook_url": webhook_url,
                "events": events,
                "secret": secret,
                "is_active": True,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            logger.info(f"Registered webhook for {merchant_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to register webhook: {e}")
            return False
