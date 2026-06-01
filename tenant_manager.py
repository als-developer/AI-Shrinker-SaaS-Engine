"""
Tenant Manager - Multi-Tenant Organization & Department Management
Hierarchical access control with budget enforcement
Version: 31.0
"""

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from core.supabase_client import supabase

logger = logging.getLogger(__name__)


class TenantManager:
    """Manage multi-tenant organizations and departments"""
    
    @staticmethod
    async def create_organization(
        name: str,
        owner_email: str,
        tier: str = "enterprise"
    ) -> Dict[str, Any]:
        """
        Create a new organization/tenant
        
        Args:
            name: Organization name
            owner_email: Owner's email address
            tier: Subscription tier
        
        Returns:
            Organization details
        """
        org_id = f"org_{uuid.uuid4().hex[:12]}"
        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        
        # Set limits based on tier
        limits = {
            "enterprise": {"max_credits": 10000, "max_users": 100, "max_api_calls": 50000},
            "business": {"max_credits": 5000, "max_users": 50, "max_api_calls": 20000},
            "startup": {"max_credits": 1000, "max_users": 10, "max_api_calls": 5000}
        }
        
        tier_limits = limits.get(tier, limits["startup"])
        
        try:
            # Create organization
            supabase.table("organizations").insert({
                "org_id": org_id,
                "company_name": name,
                "owner_email": owner_email,
                "billing_status": "active",
                "max_monthly_credits": tier_limits["max_credits"],
                "credits_used": 0,
                "tier": tier,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            # Create owner user
            supabase.table("user_workspaces").insert({
                "user_id": user_id,
                "org_id": org_id,
                "role": "admin",
                "user_email": owner_email,
                "access_clearance": "level_3",
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            logger.info(f"Created organization {org_id}: {name}")
            
            return {
                "org_id": org_id,
                "owner_id": user_id,
                "name": name,
                "tier": tier,
                "max_credits": tier_limits["max_credits"]
            }
            
        except Exception as e:
            logger.error(f"Organization creation failed: {e}")
            return {"error": str(e)}
    
    @staticmethod
    async def create_department(
        org_id: str,
        name: str,
        budget_cap_usd: float = 500.0
    ) -> Optional[str]:
        """
        Create a department within an organization
        
        Args:
            org_id: Organization ID
            name: Department name
            budget_cap_usd: Monthly budget cap
        
        Returns:
            Department ID or None
        """
        dept_id = f"dept_{uuid.uuid4().hex[:12]}"
        
        try:
            supabase.table("company_departments").insert({
                "dept_id": dept_id,
                "org_id": org_id,
                "department_name": name,
                "monthly_budget_cap_usd": budget_cap_usd,
                "credits_consumed_usd": 0,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            logger.info(f"Created department {dept_id} for org {org_id}")
            return dept_id
            
        except Exception as e:
            logger.error(f"Department creation failed: {e}")
            return None
    
    @staticmethod
    async def add_team_member(
        org_id: str,
        email: str,
        role: str = "member",
        dept_id: Optional[str] = None
    ) -> bool:
        """
        Add a team member to organization
        
        Args:
            org_id: Organization ID
            email: User email
            role: Role (admin, manager, member)
            dept_id: Optional department assignment
        
        Returns:
            True if successful
        """
        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        
        clearance_map = {
            "admin": "level_3",
            "manager": "level_2",
            "member": "level_1"
        }
        
        try:
            supabase.table("user_workspaces").insert({
                "user_id": user_id,
                "org_id": org_id,
                "dept_id": dept_id,
                "role": role,
                "user_email": email,
                "access_clearance": clearance_map.get(role, "level_1"),
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            logger.info(f"Added team member {email} to org {org_id}")
            return True
            
        except Exception as e:
            logger.error(f"Team member addition failed: {e}")
            return False
    
    @staticmethod
    async def check_budget(org_id: str, amount_usd: float) -> bool:
        """
        Check if organization has sufficient budget
        
        Args:
            org_id: Organization ID
            amount_usd: Amount to check
        
        Returns:
            True if sufficient budget
        """
        try:
            result = supabase.table("organizations").select("max_monthly_credits", "credits_used").eq("org_id", org_id).execute()
            
            if not result.data:
                return False
            
            org = result.data[0]
            remaining = float(org["max_monthly_credits"]) - float(org.get("credits_used", 0))
            
            return remaining >= amount_usd
            
        except Exception as e:
            logger.error(f"Budget check failed: {e}")
            return False
