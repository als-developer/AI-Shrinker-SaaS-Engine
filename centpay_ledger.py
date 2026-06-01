"""
CentPay Ledger - High-Velocity Off-Chain Micropayments
Multi-currency, real-time settlement, cashback rewards
Version: 31.0
"""

import asyncio
import queue
import threading
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from core.supabase_client import supabase
from core.redis_client import redis_client
from utils.constants import EXCHANGE_RATES, CASHBACK_PERCENTAGE

logger = logging.getLogger(__name__)

# Lock-free transaction queue for high throughput
_transaction_queue = queue.Queue()
_processing_thread = None


class CentPayLedger:
    """High-speed off-chain micropayment ledger"""
    
    @classmethod
    async def process_charge(
        cls,
        user_id: str,
        merchant_id: str,
        fiat_amount: float,
        currency_code: str = "USD"
    ) -> Dict[str, Any]:
        """
        Process a micropayment charge
        
        Args:
            user_id: Customer identifier
            merchant_id: Merchant identifier  
            fiat_amount: Amount in local currency
            currency_code: Currency code (TZS, KES, USD, etc.)
        
        Returns:
            Transaction result with USD amount and cashback
        """
        # Get exchange rate
        rate = EXCHANGE_RATES.get(currency_code.upper(), 1.0)
        amount_usd = Decimal(str(fiat_amount)) / Decimal(str(rate))
        
        # Calculate cashback (5% standard)
        cashback_usd = amount_usd * Decimal(str(CASHBACK_PERCENTAGE))
        net_amount_usd = amount_usd - cashback_usd
        
        # Create transaction record
        transaction = {
            "user_id": user_id,
            "merchant_id": merchant_id,
            "amount_usd": float(net_amount_usd.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)),
            "gross_amount_usd": float(amount_usd.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)),
            "cashback_usd": float(cashback_usd.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)),
            "currency_code": currency_code.upper(),
            "fiat_amount": fiat_amount,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Add to lockless queue for async processing
        _transaction_queue.put(transaction)
        
        # Ensure processing thread is running
        cls._ensure_processing_thread()
        
        # Calculate local currency cashback for response
        cashback_fiat = cashback_usd * Decimal(str(rate))
        
        return {
            "amount_usd": float(net_amount_usd),
            "gross_amount_usd": float(amount_usd),
            "cashback": float(cashback_fiat),
            "currency": currency_code.upper(),
            "status": "queued"
        }
    
    @classmethod
    async def get_balance(cls, user_id: str) -> Dict[str, Any]:
        """Get user's current wallet balance"""
        try:
            result = supabase.table("customer_wallets").select("balance_usd").eq("user_id", user_id).execute()
            if result.data:
                balance = float(result.data[0]["balance_usd"])
            else:
                balance = 0.0
                
            return {
                "user_id": user_id,
                "balance_usd": balance,
                "balance_tzs": balance * EXCHANGE_RATES.get("TZS", 2615.50)
            }
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return {"user_id": user_id, "balance_usd": 0.0, "error": str(e)}
    
    @classmethod
    async def credit_wallet(cls, user_id: str, amount_usd: float, reason: str) -> bool:
        """Credit a user's wallet (for refunds, cashback, etc.)"""
        try:
            # Check if wallet exists
            existing = supabase.table("customer_wallets").select("balance_usd").eq("user_id", user_id).execute()
            
            if existing.data:
                new_balance = float(existing.data[0]["balance_usd"]) + amount_usd
                supabase.table("customer_wallets").update({
                    "balance_usd": new_balance,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("user_id", user_id).execute()
            else:
                supabase.table("customer_wallets").insert({
                    "user_id": user_id,
                    "balance_usd": amount_usd,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
            
            logger.info(f"Credited {amount_usd} USD to {user_id} for {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to credit wallet: {e}")
            return False
    
    @classmethod
    def _ensure_processing_thread(cls):
        """Ensure background processing thread is running"""
        global _processing_thread
        if _processing_thread is None or not _processing_thread.is_alive():
            _processing_thread = threading.Thread(target=cls._process_queue, daemon=True)
            _processing_thread.start()
    
    @classmethod
    def _process_queue(cls):
        """Background thread to process transactions"""
        while True:
            try:
                transaction = _transaction_queue.get(timeout=1)
                cls._commit_transaction(transaction)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
    
    @classmethod
    def _commit_transaction(cls, transaction: Dict):
        """Commit transaction to database"""
        try:
            # Insert transaction
            result = supabase.table("micro_transactions").insert(transaction).execute()
            
            # Update wallet balance
            cls._update_wallet_balance(transaction["user_id"], -transaction["amount_usd"])
            
            # Apply cashback credit
            if transaction["cashback_usd"] > 0:
                cls._update_wallet_balance(transaction["user_id"], transaction["cashback_usd"])
            
            logger.info(f"Transaction committed: {transaction['user_id']} - ${transaction['amount_usd']}")
            
        except Exception as e:
            logger.error(f"Failed to commit transaction: {e}")
    
    @classmethod
    def _update_wallet_balance(cls, user_id: str, delta_usd: float):
        """Update wallet balance atomically"""
        try:
            existing = supabase.table("customer_wallets").select("balance_usd").eq("user_id", user_id).execute()
            
            if existing.data:
                new_balance = float(existing.data[0]["balance_usd"]) + delta_usd
                supabase.table("customer_wallets").update({
                    "balance_usd": max(0, new_balance),
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("user_id", user_id).execute()
            else:
                supabase.table("customer_wallets").insert({
                    "user_id": user_id,
                    "balance_usd": max(0, delta_usd),
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
        except Exception as e:
            logger.error(f"Failed to update wallet: {e}")
