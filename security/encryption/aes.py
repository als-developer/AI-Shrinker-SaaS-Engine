"""
AES-256 Encryption Module - Fernet Symmetric Encryption
For encrypting sensitive data at rest
Version: 31.0
"""

import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.primitives import hashes
import os
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class AESEncryption:
    """AES-256 encryption using Fernet (symmetric)"""
    
    # Master encryption key (should be from environment variable)
    MASTER_KEY = os.getenv("ENCRYPTION_KEY", "")
    
    @classmethod
    def _get_cipher(cls, salt: bytes = None) -> Fernet:
        """Get Fernet cipher instance"""
        if not cls.MASTER_KEY:
            raise ValueError("ENCRYPTION_KEY not set in environment")
        
        if salt:
            # Derive key from master key and salt
            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(cls.MASTER_KEY.encode()))
            return Fernet(key)
        else:
            return Fernet(cls.MASTER_KEY.encode())
    
    @classmethod
    def encrypt(cls, data: str) -> Tuple[str, str]:
        """
        Encrypt data with AES-256
        
        Args:
            data: String data to encrypt
        
        Returns:
            Tuple of (encrypted_data_base64, salt_base64)
        """
        try:
            # Generate random salt
            salt = os.urandom(16)
            
            # Get cipher with salt
            cipher = cls._get_cipher(salt)
            
            # Encrypt
            encrypted = cipher.encrypt(data.encode())
            
            # Return as base64 strings
            return (
                base64.urlsafe_b64encode(encrypted).decode(),
                base64.urlsafe_b64encode(salt).decode()
            )
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError(f"Encryption failed: {e}")
    
    @classmethod
    def decrypt(cls, encrypted_data_b64: str, salt_b64: str) -> str:
        """
        Decrypt data
        
        Args:
            encrypted_data_b64: Base64 encoded encrypted data
            salt_b64: Base64 encoded salt used for encryption
        
        Returns:
            Decrypted string
        """
        try:
            # Decode base64
            encrypted = base64.urlsafe_b64decode(encrypted_data_b64)
            salt = base64.urlsafe_b64decode(salt_b64)
            
            # Get cipher with salt
            cipher = cls._get_cipher(salt)
            
            # Decrypt
            decrypted = cipher.decrypt(encrypted)
            
            return decrypted.decode()
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError(f"Decryption failed: {e}")
    
    @classmethod
    def encrypt_dict(cls, data: dict, fields: list) -> dict:
        """
        Encrypt specific fields in a dictionary
        
        Args:
            data: Dictionary containing data
            fields: List of field names to encrypt
        
        Returns:
            Dictionary with encrypted fields
        """
        result = data.copy()
        
        for field in fields:
            if field in result and result[field]:
                encrypted_value, salt = cls.encrypt(str(result[field]))
                result[field] = encrypted_value
                result[f"{field}_salt"] = salt
        
        return result
    
    @classmethod
    def decrypt_dict(cls, data: dict, fields: list) -> dict:
        """
        Decrypt specific fields in a dictionary
        
        Args:
            data: Dictionary containing encrypted data
            fields: List of field names to decrypt
        
        Returns:
            Dictionary with decrypted fields
        """
        result = data.copy()
        
        for field in fields:
            if field in result and result[field]:
                salt_field = f"{field}_salt"
                if salt_field in result and result[salt_field]:
                    decrypted = cls.decrypt(result[field], result[salt_field])
                    result[field] = decrypted
        
        return result
