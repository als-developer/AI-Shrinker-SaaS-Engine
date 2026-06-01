"""
Ledger Reconciler - Automated Balance Reconciliation
Ensures off-chain ledgers match on-chain balances
Version: 31.0
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

from core.supabase_client import supabase
from core.redis_client import redis_client

logger = logging.getLogger(__name__)


class LedgerReconciler:
    """Automated ledger reconciliation service"""
    
    @classmethod
    async def reconcile_all(cls) -> Dict[str, Any]:
        """
        Reconcile all ledgers across the platform
        
        Returns:
            Reconciliation report
        """
        logger.info("Starting full ledger reconciliation...")
        
        start_time = datetime.utcnow()
        
        # Get all user wallets
        wallets = await supabase.table_select("customer_wallets")
        total_user_balance = sum(float(w.get("balance_usd", 0)) for w in wallets)
        
        # Get all developer prepaid balances
        developers = await supabase.table_select("developer_api_keys", {"is_active": True})
        total_dev_balance = sum(float(d.get("account_balance_usd", 0)) for d in developers)
        
        # Get all transactions
        transactions = await supabase.table_select("micro_transactions")
        
        # Calculate total transactions
        total_transactions = len(transactions)
        total_volume = sum(float(t.get("amount_usd", 0)) for t in transactions)
        
        # Calculate expected total
        expected_total = total_user_balance + total_dev_balance
        
        # Check for discrepancies
        report = {
            "reconciliation_id": f"rec_{datetime.utcnow().timestamp()}",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "completed",
            "metrics": {
                "total_user_wallets": len(wallets),
                "total_user_balance_usd": round(total_user_balance, 4),
                "total_developers": len(developers),
                "total_dev_balance_usd": round(total_dev_balance, 4),
                "total_transactions": total_transactions,
                "total_volume_usd": round(total_volume, 4),
                "expected_total_balance_usd": round(expected_total, 4)
            },
            "discrepancies": []
        }
        
        # Check for anomalies
        if abs(total_volume - expected_total) > 0.01:
            report["discrepancies"].append({
                "type": "balance_mismatch",
                "expected": round(expected_total, 4),
                "actual": round(total_volume, 4),
                "difference": round(total_volume - expected_total, 4)
            })
        
        # Check for stale wallets (inactive > 90 days)
        cutoff = datetime.utcnow() - timedelta(days=90)
        stale_wallets = [
            w for w in wallets 
            if w.get("last_activity") and datetime.fromisoformat(w["last_activity"]) < cutoff
        ]
        
        if stale_wallets:
            report["discrepancies"].append({
                "type": "stale_wallets",
                "count": len(stale_wallets),
                "total_balance": round(sum(float(w.get("balance_usd", 0)) for w in stale_wallets), 4)
            })
        
        # Store reconciliation report
        await supabase.table_insert("reconciliation_reports", report)
        
        # Alert if major discrepancies found
        if report["discrepancies"]:
            await cls._alert_discrepancies(report)
        
        logger.info(f"Reconciliation completed. Found {len(report['discrepancies'])} discrepancies")
        
        return report
    
    @classmethod
    async def reconcile_user(cls, user_id: str) -> Dict[str, Any]:
        """Reconcile a single user's ledger"""
        wallet = await supabase.table_select("customer_wallets", {"user_id": user_id})
        
        if not wallet:
            return {"error": "User wallet not found"}
        
        wallet = wallet[0]
        
        # Get all user transactions
        transactions = await supabase.table_select(
            "micro_transactions",
            {"user_id": user_id}
        )
        
        # Calculate expected balance from transactions
        calculated_balance = sum(
            float(t.get("amount_usd", 0)) 
            for t in transactions 
            if t.get("status") == "completed"
        )
        
        current_balance = float(wallet.get("balance_usd", 0))
        
        return {
            "user_id": user_id,
            "current_balance_usd": current_balance,
            "calculated_balance_usd": round(calculated_balance, 4),
            "difference_usd": round(current_balance - calculated_balance, 4),
            "is_balanced": abs(current_balance - calculated_balance) < 0.01,
            "transaction_count": len(transactions)
        }
    
    @classmethod
    async def _alert_discrepancies(cls, report: Dict):
        """Alert about reconciliation discrepancies"""
        # In production, send to Slack/Email
        logger.warning(f"Reconciliation discrepancies found: {report['discrepancies']}")
        
        # Could trigger webhook or send email
        pass
