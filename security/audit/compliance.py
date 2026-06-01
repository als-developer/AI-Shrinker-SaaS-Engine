
"""
Compliance Checking Module - GDPR, HIPAA, PCI-DSS
For regulatory compliance verification
Version: 31.0
"""

import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging

from core.supabase_client import supabase

logger = logging.getLogger(__name__)


class ComplianceChecker:
    """Regulatory compliance verification"""
    
    # PII patterns for data detection
    PII_PATTERNS = {
        "email": re.compile(r'[\w\.-]+@[\w\.-]+\.\w+'),
        "phone": re.compile(r'\+?[\d\s\-\(\)]{8,20}'),
        "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        "credit_card": re.compile(r'\b(?:\d[ -]*?){13,16}\b'),
        "passport": re.compile(r'\b[A-Z]{1,2}\d{6,9}\b'),
        "driver_license": re.compile(r'\b[A-Z0-9]{6,12}\b', re.I),
        "address": re.compile(r'\b\d+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b', re.I),
        "dob": re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'),
        "ip_address": re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    }
    
    @classmethod
    def detect_pii(cls, text: str) -> Dict[str, List[str]]:
        """
        Detect PII in text
        
        Args:
            text: Text to scan
        
        Returns:
            Dictionary of PII types and found values
        """
        results = {}
        
        for pii_type, pattern in cls.PII_PATTERNS.items():
            matches = pattern.findall(text)
            if matches:
                results[pii_type] = matches
        
        return results
    
    @classmethod
    def redact_pii(cls, text: str, replacement: str = "[REDACTED]") -> str:
        """Redact all PII from text"""
        result = text
        
        for pii_type, pattern in cls.PII_PATTERNS.items():
            result = pattern.sub(replacement, result)
        
        return result
    
    @classmethod
    async def check_gdpr_compliance(cls, user_id: str) -> Dict[str, bool]:
        """
        Check GDPR compliance for a user
        
        Returns:
            Dict of compliance checks
        """
        results = {
            "consent_obtained": False,
            "data_portability_ready": False,
            "right_to_be_forgotten": False,
            "breach_notification_ready": False,
            "dpa_signed": False
        }
        
        try:
            # Check user consent
            user = await supabase.table_select("user_profiles", {"id": user_id})
            if user and user[0].get("consent_given"):
                results["consent_obtained"] = True
            
            # Check data export availability
            exports = await supabase.table_select("data_exports", {"user_id": user_id})
            results["data_portability_ready"] = len(exports) > 0
            
            # Check data retention policy
            # Users have right to deletion after 30 days of inactivity
            last_login = user[0].get("last_login_at") if user else None
            if last_login:
                last_login_date = datetime.fromisoformat(last_login)
                if datetime.utcnow() - last_login_date > timedelta(days=30):
                    results["right_to_be_forgotten"] = True
            
            return results
            
        except Exception as e:
            logger.error(f"GDPR compliance check failed: {e}")
            return results
    
    @classmethod
    def get_data_retention_policy(cls, data_type: str) -> int:
        """
        Get retention period in days for different data types
        
        Args:
            data_type: Type of data (audit_logs, transactions, user_data, etc.)
        
        Returns:
            Retention period in days
        """
        policies = {
            "audit_logs": 365,      # 1 year
            "security_events": 730,  # 2 years
            "transactions": 2555,    # 7 years (tax compliance)
            "user_data": 1095,       # 3 years
            "api_logs": 90,          # 90 days
            "sessions": 30           # 30 days
        }
        
        return policies.get(data_type, 90)
    
    @classmethod
    def is_data_breach_notifiable(cls, data_scope: Dict) -> Tuple[bool, str]:
        """
        Determine if a data breach requires notification
        
        Args:
            data_scope: Data affected by breach
        
        Returns:
            Tuple of (needs_notification, reason)
        """
        # Check if PII was exposed
        if "pii" in data_scope.get("data_types", []):
            return True, "Personally Identifiable Information (PII) exposed"
        
        # Check if financial data was exposed
        if "financial" in data_scope.get("data_types", []):
            return True, "Financial data exposed"
        
        # Check number of affected users
        if data_scope.get("affected_users", 0) > 100:
            return True, f"{data_scope.get('affected_users')} users affected"
        
        return False, "Below notification threshold"
