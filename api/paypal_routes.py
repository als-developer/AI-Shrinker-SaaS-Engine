"""
PayPal Routes - Payment Gateway Endpoints
Handles payment creation, capture, and webhooks
Version: 31.0
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from services.paypal_client import PayPalClient
from services.centpay_ledger import CentPayLedger
from core.auth import authenticate_developer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/paypal", tags=["PayPal Payments"])


class CreatePaymentRequest(BaseModel):
    amount: float
    currency: str = "USD"
    description: str = "Sovereign Grid API Credits"
    return_url: Optional[str] = None
    cancel_url: Optional[str] = None
    user_id: str


class CreateSubscriptionRequest(BaseModel):
    plan_id: str
    return_url: Optional[str] = None
    cancel_url: Optional[str] = None
    user_id: str


@router.post("/create-order")
async def create_paypal_order(
    request: CreatePaymentRequest,
    developer_id: str = Depends(authenticate_developer)
):
    """
    Create a PayPal order for payment
    """
    try:
        order = await PayPalClient.create_order(
            amount=request.amount,
            currency=request.currency,
            description=request.description,
            return_url=request.return_url,
            cancel_url=request.cancel_url
        )
        
        return {
            "success": True,
            "order_id": order["order_id"],
            "approval_url": order["approval_url"],
            "amount": order["amount"],
            "currency": order["currency"]
        }
    
    except Exception as e:
        logger.error(f"PayPal order creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capture-order/{order_id}")
async def capture_paypal_order(
    order_id: str,
    user_id: str,
    developer_id: str = Depends(authenticate_developer)
):
    """
    Capture a PayPal order after customer approval
    """
    try:
        # Capture the order
        capture = await PayPalClient.capture_order(order_id)
        
        if capture["status"] != "COMPLETED":
            raise HTTPException(status_code=400, detail="Payment not completed")
        
        # Credit the user's wallet
        await CentPayLedger.credit_wallet(
            user_id=user_id,
            amount_usd=capture["amount"],
            reason=f"PayPal payment: {capture['capture_id']}"
        )
        
        # Store transaction record
        from core.supabase_client import supabase
        await supabase.table_insert("paypal_transactions", {
            "order_id": order_id,
            "capture_id": capture["capture_id"],
            "user_id": user_id,
            "amount_usd": capture["amount"],
            "payer_email": capture.get("payer_email"),
            "payer_name": capture.get("payer_name"),
            "status": "completed",
            "created_at": capture["captured_at"]
        })
        
        return {
            "success": True,
            "capture_id": capture["capture_id"],
            "amount": capture["amount"],
            "message": "Payment completed successfully"
        }
    
    except Exception as e:
        logger.error(f"PayPal capture error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def paypal_webhook(request: Request):
    """
    PayPal webhook handler for asynchronous events
    """
    try:
        # Get webhook payload
        payload = await request.json()
        event_type = payload.get("event_type")
        
        logger.info(f"Received PayPal webhook: {event_type}")
        
        # Handle different event types
        if event_type == "PAYMENT.CAPTURE.COMPLETED":
            resource = payload.get("resource", {})
            order_id = resource.get("supplementary_data", {}).get("related_ids", {}).get("order_id")
            capture_id = resource.get("id")
            
            # Update transaction status
            from core.supabase_client import supabase
            await supabase.table_update(
                "paypal_transactions",
                {"status": "completed", "webhook_processed_at": datetime.utcnow().isoformat()},
                {"capture_id": capture_id}
            )
            
        elif event_type == "PAYMENT.CAPTURE.REFUNDED":
            resource = payload.get("resource", {})
            capture_id = resource.get("links", [{}])[0].get("href", "").split("/")[-2] if resource.get("links") else None
            
            if capture_id:
                from core.supabase_client import supabase
                await supabase.table_update(
                    "paypal_transactions",
                    {"status": "refunded"},
                    {"capture_id": capture_id}
                )
        
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"PayPal webhook error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/refund/{capture_id}")
async def refund_paypal_payment(
    capture_id: str,
    amount: Optional[float] = None,
    developer_id: str = Depends(authenticate_developer)
):
    """
    Refund a PayPal payment
    """
    try:
        refund = await PayPalClient.refund_payment(capture_id, amount)
        
        # Update transaction status
        from core.supabase_client import supabase
        await supabase.table_update(
            "paypal_transactions",
            {"status": "refunded", "refund_id": refund["refund_id"]},
            {"capture_id": capture_id}
        )
        
        return {
            "success": True,
            "refund_id": refund["refund_id"],
            "amount": refund["amount"],
            "status": refund["status"]
        }
    
    except Exception as e:
        logger.error(f"PayPal refund error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-subscription")
async def create_subscription(
    request: CreateSubscriptionRequest,
    developer_id: str = Depends(authenticate_developer)
):
    """
    Create a PayPal subscription
    """
    try:
        subscription = await PayPalClient.create_subscription(
            plan_id=request.plan_id,
            return_url=request.return_url,
            cancel_url=request.cancel_url
        )
        
        return {
            "success": True,
            "subscription_id": subscription["subscription_id"],
            "approval_url": subscription["approval_url"],
            "status": subscription["status"]
        }
    
    except Exception as e:
        logger.error(f"Subscription creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subscription/{subscription_id}")
async def get_subscription_details(
    subscription_id: str,
    developer_id: str = Depends(authenticate_developer)
):
    """
    Get PayPal subscription details
    """
    try:
        details = await PayPalClient.get_subscription_details(subscription_id)
        return {"success": True, "subscription": details}
    
    except Exception as e:
        logger.error(f"Get subscription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subscription/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: str,
    reason: str = "Cancelled by user",
    developer_id: str = Depends(authenticate_developer)
):
    """
    Cancel a PayPal subscription
    """
    try:
        success = await PayPalClient.cancel_subscription(subscription_id, reason)
        
        if not success:
            raise HTTPException(status_code=400, detail="Cancellation failed")
        
        return {"success": True, "message": "Subscription cancelled successfully"}
    
    except Exception as e:
        logger.error(f"Cancel subscription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
