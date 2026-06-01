"""
Budget Enforcer - Automatic Budget Ceiling Enforcement
Prevents overspending across departments and organizations
Version: 31.0
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal

from core.supabase_client import supabase
from core.redis_client import redis_client

logger = logging.getLogger(__name__)


class BudgetEnforcer:
    """Enforce budget limits across organizational hierarchy"""
    
    # Budget cache TTL (seconds)
    CACHE_TTL = 300
    
    @classmethod
    async def check_and_consume(
        cls,
        org_id: str,
        amount_usd: float,
        user_id: Optional[str] = None,
        dept_id: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check budget and consume if available
        
        Args:
            org_id: Organization ID
            amount_usd: Amount to consume
            user_id: Optional user ID for per-user limits
            dept_id: Optional department ID
            
        Returns:
            Tuple of (success, budget_info)
        """
        # Check Redis cache first for performance
        cache_key = f"budget:{org_id}:{dept_id or 'org'}"
        cached = redis_client.get(cache_key)
        
        if cached:
            budget_info = eval(cached)  # Use json.loads in production
            if budget_info.get("remaining", 0) >= amount_usd:
                # Update Redis cache
                budget_info["remaining"] -= amount_usd
                redis_client.setex(cache_key, cls.CACHE_TTL, str(budget_info))
                return True, budget_info
        
        # Check database
        try:
            # Get organization limits
            org_result = supabase.table("organizations").select(
                "max_monthly_credits", "credits_used"
            ).eq("org_id", org_id).execute()
            
            if not org_result.data:
                return False, {"error": "Organization not found"}
            
            org = org_result.data[0]
            org_max = float(org["max_monthly_credits"])
            org_used = float(org.get("credits_used", 0))
            org_remaining = org_max - org_used
            
            # Check department limits if applicable
            dept_remaining = None
            if dept_id:
                dept_result = supabase.table("company_departments").select(
                    "monthly_budget_cap_usd", "credits_consumed_usd"
                ).eq("dept_id", dept_id).execute()
                
                if dept_result.data:
                    dept = dept_result.data[0]
                    dept_max = float(dept["monthly_budget_cap_usd"])
                    dept_used = float(dept.get("credits_consumed_usd", 0))
                    dept_remaining = dept_max - dept_used
            
            # Check if sufficient budget
            if org_remaining < amount_usd:
                return False, {
                    "remaining": org_remaining,
                    "limit": org_max,
                    "used": org_used,
                    "level": "organization"
                }
            
            if dept_remaining is not None and dept_remaining < amount_usd:
                return False, {
                    "remaining": dept_remaining,
                    "limit": dept_max,
                    "used": dept_used,
                    "level": "department"
                }
            
            # Consume budget
            new_org_used = org_used + amount_usd
            supabase.table("organizations").update({
                "credits_used": new_org_used
            }).eq("org_id", org_id).execute()
            
            if dept_id and dept_remaining is not None:
                new_dept_used = dept_used + amount_usd
                supabase.table("company_departments").update({
                    "credits_consumed_usd": new_dept_used
                }).eq("dept_id", dept_id).execute()
            
            # Log consumption
            await cls._log_consumption(org_id, dept_id, user_id, amount_usd)
            
            # Update cache
            budget_info = {
                "org_remaining": org_remaining - amount_usd,
                "org_limit": org_max,
                "org_used": new_org_used,
                "dept_remaining": dept_remaining - amount_usd if dept_remaining else None
            }
            redis_client.setex(cache_key, cls.CACHE_TTL, str(budget_info))
            
            return True, budget_info
            
        except Exception as e:
            logger.error(f"Budget enforcement error: {e}")
            return False, {"error": str(e)}
    
    @classmethod
    async def _log_consumption(
        cls,
        org_id: str,
        dept_id: Optional[str],
        user_id: Optional[str],
        amount_usd: float
    ):
        """Log budget consumption for audit"""
        try:
            supabase.table("budget_consumption_logs").insert({
                "org_id": org_id,
                "dept_id": dept_id,
                "user_id": user_id,
                "amount_usd": amount_usd,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            logger.warning(f"Failed to log consumption: {e}")
    
    @classmethod
    async def get_remaining_budget(cls, org_id: str, dept_id: Optional[str] = None) -> Dict[str, float]:
        """Get remaining budget for organization or department"""
        try:
            org_result = supabase.table("organizations").select(
                "max_monthly_credits", "credits_used"
            ).eq("org_id", org_id).execute()
            
            if not org_result.data:
                return {"error": "Organization not found"}
            
            org = org_result.data[0]
            org_remaining = float(org["max_monthly_credits"]) - float(org.get("credits_used", 0))
            
            result = {
                "org_remaining": org_remaining,
                "org_limit": float(org["max_monthly_credits"])
            }
            
            if dept_id:
                dept_result = supabase.table("company_departments").select(
                    "monthly_budget_cap_usd", "credits_consumed_usd"
                ).eq("dept_id", dept_id).execute()
                
                if dept_result.data:
                    dept = dept_result.data[0]
                    dept_remaining = float(dept["monthly_budget_cap_usd"]) - float(dept.get("credits_consumed_usd", 0))
                    result["dept_remaining"] = dept_remaining
                    result["dept_limit"] = float(dept["monthly_budget_cap_usd"])
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get budget: {e}")
            return {"error": str(e)}
