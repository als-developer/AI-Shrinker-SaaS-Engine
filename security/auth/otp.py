"""
One-Time Password Module - Time-based and HMAC-based OTP
For email verification, password reset, and login codes
Version: 31.0
"""

import secrets
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Tuple, Optional
import logging

from core.redis_client import redis_client
from services.email_sender import EmailSender

logger = logging.getLogger(__name__)


class OTPManager:
    """One-Time Password generation and verification"""
    
    # OTP configuration
    OTP_LENGTH = 6
    OTP_EXPIRY_SECONDS = 600  # 10 minutes
    MAX_ATTEMPTS = 5
    
    @classmethod
    def generate_otp(cls) -> str:
        """Generate a numeric OTP"""
        # Generate random 6-digit number
        otp = ''.join([str(secrets.randbelow(10)) for _ in range(cls.OTP_LENGTH)])
        return otp
    
    @classmethod
    def generate_hotp(cls, secret: str, counter: int) -> str:
        """
        Generate HMAC-based OTP (HOTP)
        
        Args:
            secret: Shared secret
            counter: Moving factor (event counter)
        
        Returns:
            6-digit HOTP code
        """
        # Decode secret
        key = base64.b32decode(secret.upper())
        
        # Convert counter to bytes
        counter_bytes = counter.to_bytes(8, 'big')
        
        # Generate HMAC-SHA1
        hmac_hash = hashlib.sha1(key + counter_bytes).digest()
        
        # Dynamic truncation
        offset = hmac_hash[-1] & 0x0f
        code = ((hmac_hash[offset] & 0x7f) << 24 |
                (hmac_hash[offset + 1] & 0xff) << 16 |
                (hmac_hash[offset + 2] & 0xff) << 8 |
                (hmac_hash[offset + 3] & 0xff))
        
        # Get 6-digit code
        otp = str(code % 10 ** cls.OTP_LENGTH).zfill(cls.OTP_LENGTH)
        
        return otp
    
    @classmethod
    async def send_verification_otp(cls, email: str, purpose: str = "verify") -> str:
        """
        Send verification OTP to email
        
        Args:
            email: Recipient email
            purpose: Purpose of OTP (verify, reset, login)
        
        Returns:
            OTP code (for testing, in production would be sent via email)
        """
        otp = cls.generate_otp()
        
        # Store OTP in Redis with expiry
        key = f"otp:{purpose}:{email}"
        redis_client.setex(key, cls.OTP_EXPIRY_SECONDS, otp)
        
        # Track attempts
        attempts_key = f"otp:attempts:{purpose}:{email}"
        redis_client.setex(attempts_key, cls.OTP_EXPIRY_SECONDS, 0)
        
        # Send email
        subject = f"Sovereign Grid - {purpose.capitalize()} Code"
        body = f"""
        <h2>Your {purpose} code</h2>
        <p>Your verification code is: <strong>{otp}</strong></p>
        <p>This code expires in {cls.OTP_EXPIRY_SECONDS // 60} minutes.</p>
        <p>If you didn't request this, please ignore this email.</p>
        """
        
        await EmailSender.send_email(email, subject, body)
        
        logger.info(f"OTP sent to {email} for {purpose}")
        return otp
    
    @classmethod
    async def verify_otp(cls, email: str, otp: str, purpose: str = "verify") -> Tuple[bool, Optional[str]]:
        """
        Verify OTP code
        
        Args:
            email: User email
            otp: OTP to verify
            purpose: Purpose of OTP
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        key = f"otp:{purpose}:{email}"
        stored_otp = redis_client.get(key)
        
        if not stored_otp:
            return False, "OTP has expired. Please request a new one."
        
        # Check attempts
        attempts_key = f"otp:attempts:{purpose}:{email}"
        attempts = int(redis_client.get(attempts_key) or 0)
        
        if attempts >= cls.MAX_ATTEMPTS:
            redis_client.delete(key)
            redis_client.delete(attempts_key)
            return False, "Too many failed attempts. Please request a new OTP."
        
        if stored_otp != otp:
            redis_client.incr(attempts_key)
            remaining = cls.MAX_ATTEMPTS - (attempts + 1)
            return False, f"Invalid OTP. {remaining} attempts remaining."
        
        # Valid OTP - clean up
        redis_client.delete(key)
        redis_client.delete(attempts_key)
        
        return True, None
    
    @classmethod
    async def generate_password_reset_token(cls, user_id: str) -> str:
        """Generate a password reset token"""
        token = secrets.token_urlsafe(32)
        
        # Store token with expiry
        key = f"password_reset:{user_id}"
        redis_client.setex(key, 3600, token)  # 1 hour expiry
        
        return token
    
    @classmethod
    async def verify_password_reset_token(cls, user_id: str, token: str) -> bool:
        """Verify password reset token"""
        key = f"password_reset:{user_id}"
        stored_token = redis_client.get(key)
        
        if not stored_token or stored_token != token:
            return False
        
        redis_client.delete(key)
        return True
