import uuid
import json
import asyncio
from typing import Dict, Any, List, Optional
from decimal import Decimal, getcontext
from datetime import datetime, timedelta

from .base_engine import BaseEngine
from ..database.models import db
from ..services.cache_service import cache
from ..utils.logger import get_logger

logger = get_logger(__name__)
getcontext().prec = 12

class CentPayEngine(BaseEngine):
    EXCHANGE_RATE_TZS_USD = Decimal("2615.50")
    PLATFORM_FEE_PERCENT = Decimal("1.5")
    CASHBACK_PERCENT = Decimal("5.0")
    MIN_TOPUP_TZS = Decimal("100")
    MAX_TRANSACTION_TZS = Decimal("1000000")
    
    def __init__(self):
        super().__init__("CentPay")
        self.wallets = {}  # In production, use Redis/DB
        self.transactions = []
    
    async def charge(
        self,
        user_id: str,
        merchant_id: str,
        amount_tzs: float
    ) -> Dict[str, Any]:
        """Process micro-payment"""
        
        amount = Decimal(str(amount_tzs))
        transaction_id = f"tx_{uuid.uuid4().hex[:16]}"
        
        # Validate amount
        if amount <= 0:
            return self._error_response(transaction_id, "Invalid amount")
        
        if amount > self.MAX_TRANSACTION_TZS:
            return self._error_response(transaction_id, f"Amount exceeds maximum {self.MAX_TRANSACTION_TZS} TZS")
        
        # Get user balance
        user_balance = await self.get_balance(user_id)
        user_balance_dec = Decimal(str(user_balance["balance_tzs"]))
        
        if user_balance_dec < amount:
            return {
                "status": "insufficient_funds",
                "balance_tzs": float(user_balance_dec),
                "required_tzs": float(amount),
                "transaction_id": transaction_id
            }
        
        # Calculate amounts
        amount_usd = amount / self.EXCHANGE_RATE_TZS_USD
        platform_fee = amount_usd * (self.PLATFORM_FEE_PERCENT / Decimal("100"))
        merchant_amount = amount_usd - platform_fee
        cashback = amount_usd * (self.CASHBACK_PERCENT / Decimal("100"))
        
        # Process transaction
        await self._debit_wallet(user_id, amount)
        await self._credit_wallet(merchant_id, merchant_amount, "usd")
        
        if cashback > 0:
            await self._credit_wallet(user_id, cashback, "usd", is_cashback=True)
        
        # Store transaction
        await self._store_transaction(
            transaction_id, user_id, merchant_id,
            amount, amount_usd, platform_fee
        )
        
        # Update metrics
        await self._update_metrics(amount, platform_fee)
        
        return {
            "status": "success",
            "transaction_id": transaction_id,
            "amount_charged_tzs": float(amount),
            "amount_charged_usd": float(round(amount_usd, 4)),
            "platform_fee_tzs": float(round(platform_fee * self.EXCHANGE_RATE_TZS_USD, 2)),
            "platform_fee_usd": float(round(platform_fee, 4)),
            "merchant_earnings_tzs": float(round(merchant_amount * self.EXCHANGE_RATE_TZS_USD, 2)),
            "merchant_earnings_usd": float(round(merchant_amount, 4)),
            "cashback_awarded_tzs": float(round(cashback * self.EXCHANGE_RATE_TZS_USD, 2)),
            "cashback_awarded_usd": float(round(cashback, 4)),
            "new_balance_tzs": float(user_balance_dec - amount),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_balance(self, user_id: str) -> Dict[str, Any]:
        """Get user wallet balance"""
        
        # Try cache
        cache_key = f"balance:{user_id}"
        cached = await cache.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Get from storage
        wallet = await self._get_wallet(user_id)
        
        balance = {
            "user_id": user_id,
            "balance_tzs": round(wallet.get("balance_tzs", 0), 2),
            "balance_usd": round(wallet.get("balance_usd", 0), 4),
            "total_spent_tzs": round(wallet.get("total_spent_tzs", 0), 2),
            "total_spent_usd": round(wallet.get("total_spent_usd", 0), 4),
            "total_cashback_tzs": round(wallet.get("total_cashback_tzs", 0), 2),
            "total_cashback_usd": round(wallet.get("total_cashback_usd", 0), 4),
            "transaction_count": wallet.get("transaction_count", 0)
        }
        
        # Cache for 60 seconds
        await cache.set(cache_key, json.dumps(balance), expire=60)
        
        return balance
    
    async def topup(self, user_id: str, amount_tzs: float) -> Dict[str, Any]:
        """Top up wallet balance"""
        
        amount = Decimal(str(amount_tzs))
        
        if amount < self.MIN_TOPUP_TZS:
            return {
                "status": "failed",
                "reason": f"Minimum topup is {self.MIN_TOPUP_TZS} TZS"
            }
        
        await self._credit_wallet(user_id, amount, "tzs")
        
        return {
            "status": "success",
            "user_id": user_id,
            "amount_added_tzs": float(amount),
            "new_balance_tzs": float((await self._get_wallet(user_id))["balance_tzs"]),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_transactions(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get user transaction history"""
        
        # In production, query from database
        user_transactions = [t for t in self.transactions if t["user_id"] == user_id]
        return user_transactions[offset:offset+limit]
    
    async def _get_wallet(self, user_id: str) -> Dict:
        """Get wallet from storage"""
        if user_id not in self.wallets:
            self.wallets[user_id] = {
                "balance_tzs": Decimal("5000"),
                "balance_usd": Decimal("1.91"),
                "total_spent_tzs": Decimal("0"),
                "total_spent_usd": Decimal("0"),
                "total_cashback_tzs": Decimal("0"),
                "total_cashback_usd": Decimal("0"),
                "transaction_count": 0
            }
        return self.wallets[user_id]
    
    async def _debit_wallet(self, user_id: str, amount: Decimal):
        """Debit wallet"""
        wallet = await self._get_wallet(user_id)
        wallet["balance_tzs"] -= amount
        wallet["total_spent_tzs"] += amount
        wallet["total_spent_usd"] += amount / self.EXCHANGE_RATE_TZS_USD
        wallet["transaction_count"] += 1
    
    async def _credit_wallet(self, user_id: str, amount: Decimal, currency: str, is_cashback: bool = False):
        """Credit wallet"""
        wallet = await self._get_wallet(user_id)
        
        if currency == "usd":
            wallet["balance_usd"] += amount
            if is_cashback:
                wallet["total_cashback_usd"] += amount
                wallet["total_cashback_tzs"] += amount * self.EXCHANGE_RATE_TZS_USD
        else:
            wallet["balance_tzs"] += amount
    
    async def _store_transaction(self, tx_id: str, user_id: str, merchant_id: str,
                                 amount_tzs: Decimal, amount_usd: Decimal, fee_usd: Decimal):
        """Store transaction"""
        transaction = {
            "tx_id": tx_id,
            "user_id": user_id,
            "merchant_id": merchant_id,
            "amount_tzs": float(amount_tzs),
            "amount_usd": float(amount_usd),
            "fee_usd": float(fee_usd),
            "status": "completed",
            "created_at": datetime.utcnow().isoformat()
        }
        self.transactions.append(transaction)
        
        # In production, store in database
        try:
            await db.execute(
                """INSERT INTO centpay_transactions 
                   (tx_id, user_id, merchant_id, amount_tzs, amount_usd, fee_usd, status, created_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                tx_id, user_id, merchant_id, float(amount_tzs), float(amount_usd),
                float(fee_usd), "completed", datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Failed to store transaction: {e}")
    
    async def _update_metrics(self, amount: Decimal, fee_usd: Decimal):
        """Update platform metrics"""
        await cache.hincrbyfloat("centpay_metrics", "total_volume_tzs", float(amount))
        await cache.hincrbyfloat("centpay_metrics", "total_fees_usd", float(fee_usd))
        await cache.hincrby("centpay_metrics", "total_transactions", 1)
    
    def _error_response(self, tx_id: str, reason: str) -> Dict:
        """Create error response"""
        return {
            "status": "failed",
            "reason": reason,
            "transaction_id": tx_id
        }
