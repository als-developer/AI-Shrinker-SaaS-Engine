"""
RSA Encryption Module - Asymmetric Key Management
For secure key exchange and digital signatures
Version: 31.0
"""

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from typing import Tuple, Optional
import base64
import logging

logger = logging.getLogger(__name__)


class RSAEncryption:
    """RSA asymmetric encryption for key exchange and signing"""
    
    @classmethod
    def generate_key_pair(cls, key_size: int = 4096) -> Tuple[str, str]:
        """
        Generate RSA key pair
        
        Args:
            key_size: Key size in bits (default 4096)
        
        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        
        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Get public key
        public_key = private_key.public_key()
        
        # Serialize public key
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem.decode(), public_pem.decode()
    
    @classmethod
    def encrypt_with_public_key(cls, data: str, public_key_pem: str) -> str:
        """
        Encrypt data using public key
        
        Args:
            data: String data to encrypt
            public_key_pem: Public key in PEM format
        
        Returns:
            Base64 encoded encrypted data
        """
        try:
            # Load public key
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode(),
                backend=default_backend()
            )
            
            # Encrypt
            encrypted = public_key.encrypt(
                data.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return base64.b64encode(encrypted).decode()
            
        except Exception as e:
            logger.error(f"RSA encryption failed: {e}")
            raise ValueError(f"Encryption failed: {e}")
    
    @classmethod
    def decrypt_with_private_key(cls, encrypted_data_b64: str, private_key_pem: str) -> str:
        """
        Decrypt data using private key
        
        Args:
            encrypted_data_b64: Base64 encoded encrypted data
            private_key_pem: Private key in PEM format
        
        Returns:
            Decrypted string
        """
        try:
            # Load private key
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode(),
                password=None,
                backend=default_backend()
            )
            
            # Decrypt
            encrypted = base64.b64decode(encrypted_data_b64)
            decrypted = private_key.decrypt(
                encrypted,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return decrypted.decode()
            
        except Exception as e:
            logger.error(f"RSA decryption failed: {e}")
            raise ValueError(f"Decryption failed: {e}")
    
    @classmethod
    def sign_data(cls, data: str, private_key_pem: str) -> str:
        """
        Sign data using private key
        
        Args:
            data: Data to sign
            private_key_pem: Private key in PEM format
        
        Returns:
            Base64 encoded signature
        """
        try:
            # Load private key
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode(),
                password=None,
                backend=default_backend()
            )
            
            # Sign
            signature = private_key.sign(
                data.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return base64.b64encode(signature).decode()
            
        except Exception as e:
            logger.error(f"Signing failed: {e}")
            raise ValueError(f"Signing failed: {e}")
    
    @classmethod
    def verify_signature(cls, data: str, signature_b64: str, public_key_pem: str) -> bool:
        """
        Verify signature using public key
        
        Args:
            data: Original data
            signature_b64: Base64 encoded signature
            public_key_pem: Public key in PEM format
        
        Returns:
            True if signature is valid
        """
        try:
            # Load public key
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode(),
                backend=default_backend()
            )
            
            # Verify
            signature = base64.b64decode(signature_b64)
            public_key.verify(
                signature,
                data.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
            
        except Exception as e:
            logger.warning(f"Signature verification failed: {e}")
            return False
