"""
Password Security Module - Argon2id Password Hashing
Industry-standard password security for user authentication
Version: 31.0
"""

import re
from typing import Tuple, Optional
from passlib.context import CryptContext
import secrets
import string
import logging

logger = logging.getLogger(__name__)

# Password hashing context using Argon2id (most secure)
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    default="argon2",
    argon2__memory_cost=102400,  # 100 MB
    argon2__time_cost=4,
    argon2__parallelism=4,
    argon2__hash_len=32,
    deprecated="auto"
)


class PasswordManager:
    """Secure password hashing and validation"""
    
    # Password requirements
    MIN_LENGTH = 12
    MAX_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL = True
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """
        Hash a password using Argon2id
        
        Args:
            password: Plain text password
        
        Returns:
            Hashed password string
        """
        if not password:
            raise ValueError("Password cannot be empty")
        
        if len(password) > cls.MAX_LENGTH:
            raise ValueError(f"Password exceeds maximum length of {cls.MAX_LENGTH}")
        
        return pwd_context.hash(password)
    
    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Stored hash to compare against
        
        Returns:
            True if password matches, False otherwise
        """
        if not plain_password or not hashed_password:
            return False
        
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    @classmethod
    def validate_password_strength(cls, password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate password strength against security requirements
        
        Args:
            password: Password to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < cls.MIN_LENGTH:
            return False, f"Password must be at least {cls.MIN_LENGTH} characters"
        
        if len(password) > cls.MAX_LENGTH:
            return False, f"Password must not exceed {cls.MAX_LENGTH} characters"
        
        if cls.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if cls.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if cls.REQUIRE_DIGITS and not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        
        if cls.REQUIRE_SPECIAL and not any(c in string.punctuation for c in password):
            return False, "Password must contain at least one special character"
        
        # Check for common patterns
        common_patterns = [
            r'password',
            r'123456',
            r'qwerty',
            r'admin',
            r'letmein',
            r'welcome',
            r'monkey',
            r'dragon'
        ]
        
        password_lower = password.lower()
        for pattern in common_patterns:
            if pattern in password_lower:
                return False, "Password contains common or easily guessable patterns"
        
        # Check for sequential characters
        if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password_lower):
            return False, "Password contains sequential letters"
        
        if re.search(r'(123|234|345|456|567|678|789|890)', password):
            return False, "Password contains sequential numbers"
        
        return True, None
    
    @classmethod
    def generate_secure_password(cls, length: int = 16) -> str:
        """
        Generate a cryptographically secure random password
        
        Args:
            length: Desired password length (default 16)
        
        Returns:
            Secure random password
        """
        if length < cls.MIN_LENGTH:
            length = cls.MIN_LENGTH
        
        alphabet = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # Ensure it meets requirements
        while True:
            is_valid, _ = cls.validate_password_strength(password)
            if is_valid:
                break
            password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        return password
    
    @classmethod
    def needs_rehash(cls, hashed_password: str) -> bool:
        """Check if password hash needs to be rehashed (e.g., for algorithm upgrade)"""
        return pwd_context.needs_update(hashed_password)
