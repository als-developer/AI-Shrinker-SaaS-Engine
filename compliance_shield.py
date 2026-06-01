"""
Compliance Shield - PII Detection & Redaction
GDPR/HIPAA compliant data masking at the edge
Version: 31.0
"""

import re
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PIIDetection:
    """PII detection result"""
    type: str
    value: str
    start_pos: int
    end_pos: int


class ComplianceShield:
    """Zero-trust PII protection engine"""
    
    # Compiled regex patterns for high performance
    _patterns = {
        "email": re.compile(r'[\w\.-]+@[\w\.-]+\.\w+', re.IGNORECASE),
        "credit_card": re.compile(r'\b(?:\d[ -]*?){13,16}\b'),
        "phone": re.compile(r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'),
        "ssn": re.compile(r'\b\d{3}[-]?\d{2}[-]?\d{4}\b'),
        "ip_address": re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
        "name": re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b'),
        "passport": re.compile(r'\b[A-Z]{1,2}\d{6,9}\b'),
        "drivers_license": re.compile(r'\b[A-Z0-9]{6,12}\b', re.IGNORECASE)
    }
    
    _mask_mapping = {
        "email": "[REDACTED_EMAIL]",
        "credit_card": "[REDACTED_CARD]",
        "phone": "[REDACTED_PHONE]",
        "ssn": "[REDACTED_SSN]",
        "ip_address": "[REDACTED_IP]",
        "name": "[REDACTED_NAME]",
        "passport": "[REDACTED_PASSPORT]",
        "drivers_license": "[REDACTED_LICENSE]"
    }
    
    @classmethod
    def scan(cls, text: str) -> List[PIIDetection]:
        """Scan text for PII"""
        detections = []
        
        for pii_type, pattern in cls._patterns.items():
            for match in pattern.finditer(text):
                detections.append(PIIDetection(
                    type=pii_type,
                    value=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        return detections
    
    @classmethod
    def redact(cls, text: str, mask_type: str = "standard") -> str:
        """
        Redact all PII from text
        
        Args:
            text: Input text to redact
            mask_type: 'standard' for placeholder or 'asterisk' for ***
        
        Returns:
            Redacted text
        """
        if not text:
            return text
        
        result = text
        
        for pii_type, pattern in cls._patterns.items():
            if mask_type == "standard":
                mask = cls._mask_mapping.get(pii_type, f"[REDACTED_{pii_type.upper()}]")
            else:
                mask = "***REDACTED***"
            
            result = pattern.sub(mask, result)
        
        return result
    
    @classmethod
    def has_pii(cls, text: str) -> bool:
        """Check if text contains any PII"""
        for pattern in cls._patterns.values():
            if pattern.search(text):
                return True
        return False
    
    @classmethod
    def get_risk_score(cls, text: str) -> Dict[str, Any]:
        """Calculate PII risk score"""
        detections = cls.scan(text)
        
        risk_weights = {
            "credit_card": 10,
            "ssn": 9,
            "passport": 8,
            "drivers_license": 7,
            "phone": 5,
            "email": 4,
            "name": 3,
            "ip_address": 2
        }
        
        total_risk = 0
        by_type = {}
        
        for detection in detections:
            weight = risk_weights.get(detection.type, 1)
            total_risk += weight
            by_type[detection.type] = by_type.get(detection.type, 0) + 1
        
        # Normalize to 0-100 scale (max risk ~50)
        risk_score = min(100, total_risk * 2)
        
        return {
            "has_pii": len(detections) > 0,
            "risk_score": risk_score,
            "detection_count": len(detections),
            "detections_by_type": by_type,
            "severity": "HIGH" if risk_score > 70 else "MEDIUM" if risk_score > 30 else "LOW"
        }
