"""
Input Validators - Data Validation Utilities
For validating email, phone, API keys, and request data
Version: 31.0
"""

import re
from typing import Tuple, Optional, Any
from email_validator import validate_email, EmailNotValidError
import phonenumbers


class InputValidator:
    """Comprehensive input validation utilities"""
    
    # Patterns
    EMAIL_PATTERN = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
    UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
    API_KEY_PATTERN = re.compile(r'^sk_sov_[a-zA-Z0-9]{32,64}$')
    HEX_COLOR_PATTERN = re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')
    
    @classmethod
    def validate_email(cls, email: str) -> Tuple[bool, Optional[str]]:
        """
        Validate email address
        
        Args:
            email: Email address to validate
        
        Returns:
            Tuple of (is_valid, normalized_email or error)
        """
        if not email:
            return False, "Email is required"
        
        try:
            valid = validate_email(email)
            return True, valid.normalized
        except EmailNotValidError as e:
            return False, str(e)
    
    @classmethod
    def validate_phone(cls, phone: str, country: str = "TZ") -> Tuple[bool, Optional[str]]:
        """
        Validate phone number
        
        Args:
            phone: Phone number to validate
            country: Country code (default TZ for Tanzania)
        
        Returns:
            Tuple of (is_valid, formatted_number or error)
        """
        if not phone:
            return False, "Phone number is required"
        
        try:
            parsed = phonenumbers.parse(phone, country)
            if phonenumbers.is_valid_number(parsed):
                formatted = phonenumbers.format_number(
                    parsed, 
                    phonenumbers.PhoneNumberFormat.E164
                )
                return True, formatted
            return False, "Invalid phone number"
        except Exception as e:
            return False, str(e)
    
    @classmethod
    def validate_api_key(cls, api_key: str) -> Tuple[bool, Optional[str]]:
        """Validate API key format"""
        if not api_key:
            return False, "API key is required"
        
        if not cls.API_KEY_PATTERN.match(api_key):
            return False, "Invalid API key format"
        
        return True, None
    
    @classmethod
    def validate_uuid(cls, uuid_str: str) -> bool:
        """Validate UUID format"""
        return bool(cls.UUID_PATTERN.match(uuid_str))
    
    @classmethod
    def validate_url(cls, url: str) -> Tuple[bool, Optional[str]]:
        """Validate URL format"""
        if not url:
            return False, "URL is required"
        
        pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.I
        )
        
        if pattern.match(url):
            return True, None
        return False, "Invalid URL format"
    
    @classmethod
    def validate_amount(cls, amount: float, min_amount: float = 0.01, max_amount: float = 1000000) -> Tuple[bool, Optional[str]]:
        """Validate monetary amount"""
        if amount <= 0:
            return False, "Amount must be positive"
        
        if amount < min_amount:
            return False, f"Amount must be at least {min_amount}"
        
        if amount > max_amount:
            return False, f"Amount cannot exceed {max_amount}"
        
        return True, None
    
    @classmethod
    def validate_text_length(cls, text: str, min_length: int = 1, max_length: int = 10000) -> Tuple[bool, Optional[str]]:
        """Validate text length"""
        if not text:
            return False, "Text is required"
        
        if len(text) < min_length:
            return False, f"Text must be at least {min_length} characters"
        
        if len(text) > max_length:
            return False, f"Text cannot exceed {max_length} characters"
        
        return True, None
    
    @classmethod
    def sanitize_input(cls, text: str) -> str:
        """Sanitize input to prevent XSS and injection"""
        if not text:
            return ""
        
        # Remove dangerous characters
        dangerous = ['<', '>', '&', '"', "'", ';', '`', '|', '$', '(', ')', '[', ']', '{', '}']
        for char in dangerous:
            text = text.replace(char, '')
        
        # Limit length
        if len(text) > 10000:
            text = text[:10000]
        
        return text.strip()
    
    @classmethod
    def validate_json_schema(cls, data: dict, required_fields: list) -> Tuple[bool, Optional[str]]:
        """Validate JSON against required fields schema"""
        missing = [field for field in required_fields if field not in data]
        
        if missing:
            return False, f"Missing required fields: {', '.join(missing)}"
        
        return True, None
