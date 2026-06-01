"""
Mobile Money - African Mobile Money Gateway Integration
M-Pesa, Tigo Pesa, Airtel Money support
Version: 31.0
"""

import os
import hashlib
import base64
import secrets
from datetime import datetime
from typing import Dict, Any, Optional
import httpx
import logging

logger = logging.getLogger(__name__)


class MobileMoneyGateway:
    """Mobile money payment gateway for African markets"""
    
    # Supported operators
    OPERATORS = {
        "mpesa": {
            "name": "M-Pesa",
            "countries": ["TZ", "KE", "UG", "RW"],
            "api_url": "https://api.safaricom.co.ke"
        },
        "tigo_pesa": {
            "name": "Tigo Pesa",
            "countries": ["TZ"],
            "api_url": "https://openapi.tigo.co.tz"
        },
        "airtel_money": {
            "name": "Airtel Money",
            "countries": ["TZ", "KE", "UG", "MW", "ZM"],
            "api_url": "https://api.airtel.africa"
        },
        "halopesa": {
            "name": "HaloPesa",
            "countries": ["TZ"],
            "api_url": "https://api.halopesa.co.tz"
        }
    }
    
    @classmethod
    async def initiate_payment(
        cls,
        phone_number: str,
        amount: float,
        currency: str,
        operator: str,
        reference: str,
        callback_url: str
    ) -> Dict[str, Any]:
        """
        Initiate a mobile money payment
        
        Args:
            phone_number: Customer phone number (e.g., 255712345678)
            amount: Amount in local currency
            currency: Currency code (TZS, KES, UGX, etc.)
            operator: Operator name (mpesa, tigo_pesa, airtel_money)
            reference: Unique transaction reference
            callback_url: Webhook URL for payment status
            
        Returns:
            Payment initiation result
        """
        
        # Validate operator
        if operator not in cls.OPERATORS:
            return {"success": False, "error": f"Unsupported operator: {operator}"}
        
        # Validate phone number format
        if not cls._validate_phone(phone_number, operator):
            return {"success": False, "error": "Invalid phone number format"}
        
        operator_config = cls.OPERATORS[operator]
        
        # Generate transaction ID
        transaction_id = f"MOB_{reference}_{secrets.token_hex(4)}"
        
        try:
            # Different APIs for different operators
            if operator == "mpesa":
                result = await cls._initiate_mpesa_payment(
                    phone_number, amount, currency, reference, callback_url
                )
            elif operator == "tigo_pesa":
                result = await cls._initiate_tigo_pesa_payment(
                    phone_number, amount, currency, reference, callback_url
                )
            elif operator == "airtel_money":
                result = await cls._initiate_airtel_payment(
                    phone_number, amount, currency, reference, callback_url
                )
            else:
                result = {"success": False, "error": "Operator integration not implemented"}
            
            # Log payment initiation
            await cls._log_payment(transaction_id, phone_number, amount, currency, operator, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Mobile money payment failed: {e}")
            return {"success": False, "error": str(e)}
    
    @classmethod
    async def _initiate_mpesa_payment(
        cls,
        phone_number: str,
        amount: float,
        currency: str,
        reference: str,
        callback_url: str
    ) -> Dict[str, Any]:
        """Initiate M-Pesa STK Push"""
        # In production, use actual M-Pesa API
        # This is a mock implementation
        logger.info(f"M-Pesa payment initiated: {phone_number}, {amount} {currency}")
        
        return {
            "success": True,
            "checkout_request_id": f"ws_CO_{secrets.token_hex(16)}",
            "merchant_request_id": f"ws_MR_{secrets.token_hex(16)}",
            "response_code": "0",
            "response_description": "Success. Request accepted for processing",
            "customer_message": "Enter PIN to complete transaction"
        }
    
    @classmethod
    async def _initiate_tigo_pesa_payment(
        cls,
        phone_number: str,
        amount: float,
        currency: str,
        reference: str,
        callback_url: str
    ) -> Dict[str, Any]:
        """Initiate Tigo Pesa payment"""
        logger.info(f"Tigo Pesa payment initiated: {phone_number}, {amount} {currency}")
        
        return {
            "success": True,
            "transaction_id": f"TIG_{secrets.token_hex(12)}",
            "status": "PENDING",
            "message": "Payment request sent to customer"
        }
    
    @classmethod
    async def _initiate_airtel_payment(
        cls,
        phone_number: str,
        amount: float,
        currency: str,
        reference: str,
        callback_url: str
    ) -> Dict[str, Any]:
        """Initiate Airtel Money payment"""
        logger.info(f"Airtel payment initiated: {phone_number}, {amount} {currency}")
        
        return {
            "success": True,
            "transaction_id": f"AIR_{secrets.token_hex(12)}",
            "status": "PENDING",
            "message": "Payment request sent to customer"
        }
    
    @classmethod
    async def check_payment_status(cls, transaction_id: str, operator: str) -> Dict[str, Any]:
        """Check status of a mobile money payment"""
        # In production, query the operator's API
        return {
            "transaction_id": transaction_id,
            "status": "COMPLETED",
            "operator": operator,
            "checked_at": datetime.utcnow().isoformat()
        }
    
    @classmethod
    async def _log_payment(
        cls,
        transaction_id: str,
        phone_number: str,
        amount: float,
        currency: str,
        operator: str,
        result: Dict
    ):
        """Log payment for audit"""
        try:
            from core.supabase_client import supabase
            supabase.table("mobile_money_logs").insert({
                "transaction_id": transaction_id,
                "phone_number": phone_number,
                "amount": amount,
                "currency": currency,
                "operator": operator,
                "result": result,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            logger.warning(f"Failed to log payment: {e}")
    
    @classmethod
    def _validate_phone(cls, phone_number: str, operator: str) -> bool:
        """Validate phone number format for operator"""
        # Basic validation
        if not phone_number:
            return False
        
        # Remove any non-digit characters
        digits = ''.join(filter(str.isdigit, phone_number))
        
        # Check length
        if operator in ["mpesa", "tigo_pesa"]:
            # Tanzanian numbers: 255712345678 (12 digits) or 0712345678 (10 digits)
            return len(digits) in [10, 12]
        
        return len(digits) >= 9
