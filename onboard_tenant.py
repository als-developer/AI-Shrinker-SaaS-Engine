"""
Tenant Onboarding - Automated Corporate Account Setup
Streamlined onboarding for enterprise clients
Version: 31.0
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from core.supabase_client import supabase
from core.redis_client import redis_client
from services.api_key_auth import APIKeyManager

logger = logging.getLogger(__name__)


class TenantOnboarding:
    """Automated onboarding for corporate tenants"""
    
    @classmethod
    async def onboard_enterprise(
        cls,
        company_name: str,
        admin_email: str,
        tier: str = "enterprise",
        initial_credits: float = 1000.0
    ) -> Dict[str, Any]:
        """
        Onboard a new enterprise tenant
        
        Args:
            company_name: Company name
            admin_email: Administrator email
            tier: Subscription tier
            initial_credits: Initial credit balance
            
        Returns:
            Tenant information
        """
        org_id = f"org_{uuid.uuid4().hex[:12]}"
        admin_id = f"usr_{uuid.uuid4().hex[:12]}"
        
        # Create organization
        await supabase.table_insert("organizations", {
            "org_id": org_id,
            "company_name": company_name,
            "owner_email": admin_email,
            "billing_status": "active",
            "max_monthly_credits": cls._get_credits_for_tier(tier),
            "credits_used": 0,
            "tier": tier,
            "created_at": datetime.utcnow().isoformat()
        })
        
        # Create admin user
        await supabase.table_insert("user_workspaces", {
            "user_id": admin_id,
            "org_id": org_id,
            "role": "admin",
            "user_email": admin_email,
            "access_clearance": "level_3",
            "created_at": datetime.utcnow().isoformat()
        })
        
        # Create API key for admin
        api_key = await APIKeyManager.create_key(
            developer_id=admin_id,
            name=f"Admin Key - {company_name}",
            initial_balance_usd=initial_credits
        )
        
        # Create default department
        dept_id = f"dept_{uuid.uuid4().hex[:12]}"
        await supabase.table_insert("company_departments", {
            "dept_id": dept_id,
            "org_id": org_id,
            "department_name": "General",
            "monthly_budget_cap_usd": cls._get_credits_for_tier(tier),
            "credits_consumed_usd": 0,
            "created_at": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Onboarded enterprise: {company_name} (org_id: {org_id})")
        
        return {
            "success": True,
            "org_id": org_id,
            "admin_id": admin_id,
            "dept_id": dept_id,
            "api_key": api_key,
            "tier": tier,
            "max_monthly_credits": cls._get_credits_for_tier(tier),
            "message": f"Enterprise account created. API key will be shown only once."
        }
    
    @classmethod
    def _get_credits_for_tier(cls, tier: str) -> float:
        """Get monthly credits for a tier"""
        tier_limits = {
            "enterprise": 10000.0,
            "business": 5000.0,
            "startup": 1000.0,
            "free": 100.0
        }
        return tier_limits.get(tier, 500.0)
    
    @classmethod
    async def add_team_member(
        cls,
        org_id: str,
        email: str,
        role: str = "member",
        department_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a team member to an organization"""
        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        
        role_clearance = {
            "admin": "level_3",
            "manager": "level_2",
            "member": "level_1"
        }
        
        await supabase.table_insert("user_workspaces", {
            "user_id": user_id,
            "org_id": org_id,
            "dept_id": department_id,
            "role": role,
            "user_email": email,
            "access_clearance": role_clearance.get(role, "level_1"),
            "created_at": datetime.utcnow().isoformat()
        })
        
        return {
            "success": True,
            "user_id": user_id,
            "email": email,
            "role": role
        }
