"""
PayPal Client - International Payment Gateway Integration
Handles PayPal payments, subscriptions, and payouts worldwide
Version: 31.0
"""

import os
import base64
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
import logging

logger = logging.getLogger(__name__)


class PayPalClient:
    """PayPal REST API client for international payments"""
    
    # PayPal API endpoints
    SANDBOX_URL = "https://api-m.sandbox.paypal.com"
    PRODUCTION_URL = "https://api-m.paypal.com"
    
    # Client credentials (your provided keys)
    CLIENT_ID = "AdYZjwcxNYqpWCglcoqt4cv0ESkJ-G3RChAAuuET"
    SECRET_KEY = "EAecZX7x2XtI61BA-b72HxH0A4xInOX6rnolchtua"
    
    # Webhook ID (to be configured after first run)
    WEBHOOK_ID = None
    
    _access_token = None
    _token_expires_at = None
    
    @classmethod
    def _get_api_url(cls) -> str:
        """Get API URL based on environment"""
        env = os.getenv("ENVIRONMENT", "development")
        if env == "production":
            return cls.PRODUCTION_URL
        return cls.SANDBOX_URL
    
    @classmethod
    async def _get_access_token(cls) -> str:
        """Get PayPal access token (with caching)"""
        import time
        
        # Check if token is still valid
        if cls._access_token and cls._token_expires_at and time.time() < cls._token_expires_at:
            return cls._access_token
        
        # Get new token
        auth_string = f"{cls.CLIENT_ID}:{cls.SECRET_KEY}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{cls._get_api_url()}/v1/oauth2/token",
                headers={
                    "Authorization": f"Basic {auth_b64}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={"grant_type": "client_credentials"}
            )
            
            if response.status_code != 200:
                logger.error(f"PayPal auth failed: {response.text}")
                raise Exception(f"PayPal authentication failed: {response.status_code}")
            
            data = response.json()
            cls._access_token = data["access_token"]
            cls._token_expires_at = time.time() + data["expires_in"] - 60  # 60s buffer
            
            logger.info("PayPal access token obtained")
            return cls._access_token
    
    @classmethod
    async def create_order(
        cls,
        amount: float,
        currency: str = "USD",
        description: str = "Sovereign Grid API Credits",
        return_url: str = None,
        cancel_url: str = None
    ) -> Dict[str, Any]:
        """
        Create a PayPal order for payment
        
        Args:
            amount: Amount to charge
            currency: Currency code (USD, EUR, GBP, etc.)
            description: Order description
            return_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancelled payment
        
        Returns:
            Order details including approval URL
        """
        token = await cls._get_access_token()
        
        # Default URLs
        base_url = os.getenv("APP_URL", "https://sovereigngrid.com")
        return_url = return_url or f"{base_url}/payment/success"
        cancel_url = cancel_url or f"{base_url}/payment/cancel"
        
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": currency.upper(),
                    "value": str(round(amount, 2))
                },
                "description": description,
                "custom_id": f"SG_{datetime.utcnow().timestamp()}"
            }],
            "application_context": {
                "return_url": return_url,
                "cancel_url": cancel_url,
                "brand_name": "Sovereign Grid",
                "landing_page": "BILLING",
                "user_action": "PAY_NOW"
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{cls._get_api_url()}/v2/checkout/orders",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if response.status_code != 201:
                logger.error(f"PayPal order creation failed: {response.text}")
                raise Exception(f"Order creation failed: {response.status_code}")
            
            order = response.json()
            
            # Extract approval URL
            approval_url = None
            for link in order.get("links", []):
                if link.get("rel") == "approve":
                    approval_url = link.get("href")
                    break
            
            return {
                "order_id": order["id"],
                "status": order["status"],
                "approval_url": approval_url,
                "amount": amount,
                "currency": currency
            }
    
    @classmethod
    async def capture_order(cls, order_id: str) -> Dict[str, Any]:
        """
        Capture a PayPal order after customer approval
        
        Args:
            order_id: PayPal order ID
        
        Returns:
            Capture details
        """
        token = await cls._get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{cls._get_api_url()}/v2/checkout/orders/{order_id}/capture",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code != 201:
                logger.error(f"PayPal capture failed: {response.text}")
                raise Exception(f"Capture failed: {response.status_code}")
            
            capture = response.json()
            
            # Extract capture details
            capture_id = None
            amount = None
            for unit in capture.get("purchase_units", []):
                for capture_detail in unit.get("payments", {}).get("captures", []):
                    capture_id = capture_detail.get("id")
                    amount = capture_detail.get("amount", {}).get("value")
            
            return {
                "capture_id": capture_id,
                "order_id": order_id,
                "status": capture["status"],
                "amount": float(amount) if amount else None,
                "payer_email": capture.get("payer", {}).get("email_address"),
                "payer_name": f"{capture.get('payer', {}).get('name', {}).get('given_name', '')} {capture.get('payer', {}).get('name', {}).get('surname', '')}",
                "captured_at": datetime.utcnow().isoformat()
            }
    
    @classmethod
    async def get_order_details(cls, order_id: str) -> Dict[str, Any]:
        """Get PayPal order details"""
        token = await cls._get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{cls._get_api_url()}/v2/checkout/orders/{order_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get order details: {response.text}")
                return {"status": "error", "message": "Order not found"}
            
            return response.json()
    
    @classmethod
    async def refund_payment(cls, capture_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """
        Refund a captured payment
        
        Args:
            capture_id: PayPal capture ID
            amount: Amount to refund (full refund if None)
        
        Returns:
            Refund details
        """
        token = await cls._get_access_token()
        
        payload = {}
        if amount:
            payload["amount"] = {
                "value": str(round(amount, 2)),
                "currency_code": "USD"
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{cls._get_api_url()}/v2/payments/captures/{capture_id}/refund",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if response.status_code != 201:
                logger.error(f"PayPal refund failed: {response.text}")
                raise Exception(f"Refund failed: {response.status_code}")
            
            refund = response.json()
            
            return {
                "refund_id": refund["id"],
                "capture_id": capture_id,
                "status": refund["status"],
                "amount": float(refund.get("amount", {}).get("value", 0)),
                "refunded_at": datetime.utcnow().isoformat()
            }
    
    @classmethod
    async def create_subscription(
        cls,
        plan_id: str,
        return_url: str = None,
        cancel_url: str = None
    ) -> Dict[str, Any]:
        """
        Create a PayPal subscription
        
        Args:
            plan_id: PayPal plan ID (created separately)
            return_url: URL after successful subscription
            cancel_url: URL after cancelled subscription
        
        Returns:
            Subscription details
        """
        token = await cls._get_access_token()
        
        base_url = os.getenv("APP_URL", "https://sovereigngrid.com")
        return_url = return_url or f"{base_url}/subscription/success"
        cancel_url = cancel_url or f"{base_url}/subscription/cancel"
        
        payload = {
            "plan_id": plan_id,
            "application_context": {
                "return_url": return_url,
                "cancel_url": cancel_url,
                "brand_name": "Sovereign Grid"
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{cls._get_api_url()}/v1/billing/subscriptions",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if response.status_code != 201:
                logger.error(f"Subscription creation failed: {response.text}")
                raise Exception(f"Subscription creation failed: {response.status_code}")
            
            subscription = response.json()
            
            # Extract approval URL
            approval_url = None
            for link in subscription.get("links", []):
                if link.get("rel") == "approve":
                    approval_url = link.get("href")
                    break
            
            return {
                "subscription_id": subscription["id"],
                "status": subscription["status"],
                "approval_url": approval_url
            }
    
    @classmethod
    async def get_subscription_details(cls, subscription_id: str) -> Dict[str, Any]:
        """Get PayPal subscription details"""
        token = await cls._get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{cls._get_api_url()}/v1/billing/subscriptions/{subscription_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get subscription: {response.text}")
                return {"status": "error"}
            
            return response.json()
    
    @classmethod
    async def cancel_subscription(cls, subscription_id: str, reason: str = "Cancelled by user") -> bool:
        """Cancel a PayPal subscription"""
        token = await cls._get_access_token()
        
        payload = {"reason": reason}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{cls._get_api_url()}/v1/billing/subscriptions/{subscription_id}/cancel",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if response.status_code != 204:
                logger.error(f"Subscription cancellation failed: {response.text}")
                return False
            
            return True
