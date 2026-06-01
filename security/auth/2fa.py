"""
Two-Factor Authentication Module - TOTP Based 2FA
Time-based One-Time Password (TOTP) implementation
Version: 31.0
"""

import pyotp
import qrcode
import base64
from io import BytesIO
from typing import Tuple, Optional, Dict
from datetime import datetime
import logging

from core.supabase_client import supabase
from core.redis_client import redis_client

logger = logging.getLogger(__name__)


class TwoFactorAuth:
    """TOTP-based two-factor authentication"""
    
    # TOTP configuration
    TOTP_INTERVAL = 30  # seconds
    TOTP_DIGITS = 6
    BACKUP_CODE_COUNT = 10
    
    @classmethod
    def generate_secret(cls, user_email: str) -> Dict[str, str]:
        """
        Generate a new TOTP secret for a user
        
        Args:
            user_email: User's email address for issuer
        
        Returns:
            Dict with secret and provisioning URI
        """
        # Generate random secret
        secret = pyotp.random_base32()
        
        # Create provisioning URI for authenticator apps
        issuer = "Sovereign Grid"
        provisioning_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=issuer
        )
        
        return {
            "secret": secret,
            "provisioning_uri": provisioning_uri
        }
    
    @classmethod
    def generate_qr_code(cls, provisioning_uri: str) -> str:
        """
        Generate QR code as base64 string for display
        
        Args:
            provisioning_uri: TOTP provisioning URI
        
        Returns:
            Base64 encoded QR code image
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_base64}"
    
    @classmethod
    def verify_totp(cls, secret: str, code: str) -> bool:
        """
        Verify TOTP code
        
        Args:
            secret: User's TOTP secret
            code: 6-digit code from authenticator app
        
        Returns:
            True if code is valid, False otherwise
        """
        if not secret or not code or len(code) != cls.TOTP_DIGITS:
            return False
        
        if not code.isdigit():
            return False
        
        totp = pyotp.TOTP(secret, interval=cls.TOTP_INTERVAL, digits=cls.TOTP_DIGITS)
        return totp.verify(code)
    
    @classmethod
    def generate_backup_codes(cls) -> list:
        """
        Generate backup codes for account recovery
        
        Returns:
            List of backup codes
        """
        import secrets
        codes = []
        for _ in range(cls.BACKUP_CODE_COUNT):
            # Generate 8-character alphanumeric code
            code = secrets.token_hex(4).upper()
            codes.append(code)
        return codes
    
    @classmethod
    async def enable_2fa(cls, user_id: str, secret: str, backup_codes: list) -> bool:
        """
        Enable 2FA for a user
        
        Args:
            user_id: User ID
            secret: TOTP secret
            backup_codes: List of backup codes
        
        Returns:
            True if enabled successfully
        """
        try:
            # Hash backup codes before storing
            from security.auth.password import PasswordManager
            hashed_backup_codes = [
                PasswordManager.hash_password(code) for code in backup_codes
            ]
            
            supabase.table("user_2fa").insert({
                "user_id": user_id,
                "secret": secret,
                "backup_codes": hashed_backup_codes,
                "is_enabled": True,
                "verified_at": datetime.utcnow().isoformat()
            }).execute()
            
            logger.info(f"2FA enabled for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable 2FA: {e}")
            return False
    
    @classmethod
    async def disable_2fa(cls, user_id: str) -> bool:
        """Disable 2FA for a user"""
        try:
            supabase.table("user_2fa").update({
                "is_enabled": False,
                "disabled_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).execute()
            
            logger.info(f"2FA disabled for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disable 2FA: {e}")
            return False
    
    @classmethod
    async def verify_backup_code(cls, user_id: str, code: str) -> bool:
        """
        Verify a backup code
        
        Args:
            user_id: User ID
            code: Backup code to verify
        
        Returns:
            True if valid, False otherwise
        """
        from security.auth.password import PasswordManager
        
        try:
            result = supabase.table("user_2fa").select("backup_codes").eq("user_id", user_id).execute()
            
            if not result.data:
                return False
            
            backup_codes = result.data[0].get("backup_codes", [])
            
            for i, hashed_code in enumerate(backup_codes):
                if PasswordManager.verify_password(code, hashed_code):
                    # Remove used backup code
                    new_codes = backup_codes[:i] + backup_codes[i+1:]
                    supabase.table("user_2fa").update({
                        "backup_codes": new_codes
                    }).eq("user_id", user_id).execute()
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Backup code verification failed: {e}")
            return False
