"""
SLA Refund Trigger - Automated SLA Compliance & Refunds
Monitors uptime and automatically issues refunds for violations
Version: 31.0
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

from core.supabase_client import supabase

logger = logging.getLogger(__name__)


class SLARefundTrigger:
    """Automated SLA compliance monitoring and refund processing"""
    
    # SLA tiers and their guarantees
    SLA_TIERS = {
        "enterprise": {
            "uptime_guarantee": 99.99,
            "refund_thresholds": {
                99.00: 0.10,   # 10% refund if below 99%
                98.00: 0.25,   # 25% refund if below 98%
                95.00: 0.50,   # 50% refund if below 95%
                0.00: 1.00     # 100% refund if below 95%
            }
        },
        "business": {
            "uptime_guarantee": 99.95,
            "refund_thresholds": {
                99.00: 0.10,
                98.00: 0.20,
                95.00: 0.40,
                0.00: 0.80
            }
        },
        "startup": {
            "uptime_guarantee": 99.90,
            "refund_thresholds": {
                99.00: 0.05,
                98.00: 0.10,
                95.00: 0.20,
                0.00: 0.50
            }
        }
    }
    
    @classmethod
    async def check_and_refund(cls, org_id: str) -> Dict[str, Any]:
        """
        Check SLA compliance and issue refund if violated
        
        Args:
            org_id: Organization ID
            
        Returns:
            Refund result
        """
        # Get organization details
        org = await supabase.table_select("organizations", {"org_id": org_id})
        if not org:
            return {"error": "Organization not found"}
        
        org = org[0]
        tier = org.get("tier", "startup")
        sla_config = cls.SLA_TIERS.get(tier, cls.SLA_TIERS["startup"])
        
        # Get uptime for current month
        uptime = await cls._calculate_monthly_uptime(org_id)
        
        # Check if SLA violated
        if uptime >= sla_config["uptime_guarantee"]:
            return {
                "org_id": org_id,
                "compliant": True,
                "uptime": uptime,
                "guarantee": sla_config["uptime_guarantee"],
                "message": "SLA requirements met"
            }
        
        # Calculate refund percentage
        refund_percentage = 0.0
        for threshold, percentage in sla_config["refund_thresholds"].items():
            if uptime < threshold:
                refund_percentage = percentage
                break
        
        # Calculate refund amount
        monthly_subscription = org.get("monthly_subscription_usd", 499.00)
        refund_amount_usd = monthly_subscription * refund_percentage
        
        # Process refund
        if refund_amount_usd > 0:
            refund_id = await cls._process_refund(org_id, refund_amount_usd, uptime)
            
            return {
                "org_id": org_id,
                "compliant": False,
                "uptime": uptime,
                "guarantee": sla_config["uptime_guarantee"],
                "refund_percentage": refund_percentage * 100,
                "refund_amount_usd": refund_amount_usd,
                "refund_id": refund_id,
                "message": f"SLA violation detected. {refund_percentage*100}% refund issued."
            }
        
        return {
            "org_id": org_id,
            "compliant": False,
            "uptime": uptime,
            "guarantee": sla_config["uptime_guarantee"],
            "refund_percentage": 0,
            "message": "SLA violation detected but no refund threshold met"
        }
    
    @classmethod
    async def _calculate_monthly_uptime(cls, org_id: str) -> float:
        """Calculate uptime percentage for current month"""
        # In production, query uptime monitoring system
        # This is a mock implementation
        import random
        return random.uniform(99.85, 100.0)
    
    @classmethod
    async def _process_refund(cls, org_id: str, amount_usd: float, uptime: float) -> str:
        """Process refund and create credit"""
        from services.centpay_ledger import CentPayLedger
        
        refund_id = f"ref_{org_id}_{datetime.utcnow().timestamp()}"
        
        # Credit the organization's wallet
        await CentPayLedger.credit_wallet(
            user_id=org_id,
            amount_usd=amount_usd,
            reason=f"SLA violation refund (uptime: {uptime}%)"
        )
        
        # Log refund
        await supabase.table_insert("sla_refunds", {
            "refund_id": refund_id,
            "org_id": org_id,
            "amount_usd": amount_usd,
            "uptime_at_time": uptime,
            "processed_at": datetime.utcnow().isoformat()
        })
        
        logger.info(f"SLA refund {refund_id} processed for {org_id}: ${amount_usd}")
        
        return refund_id
    
    @classmethod
    async def get_org_sla_history(cls, org_id: str) -> list:
        """Get SLA history for an organization"""
        refunds = await supabase.table_select("sla_refunds", {"org_id": org_id})
        return refunds
