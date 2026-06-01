"""
Unit Tests - Authentication Module
Testing JWT, password hashing, 2FA, and session management
Version: 31.0
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
import jwt
from unittest.mock import AsyncMock, Mock, patch

from security.auth.password import PasswordManager
from security.auth.session import SessionManager
from security.auth.otp import OTPManager
from security.auth.two_factor import TwoFactorAuth
from security.encryption.jwt import JWTManager


class TestPasswordManager:
    """Tests for password hashing and validation"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "SecurePass123!"
        hashed = PasswordManager.hash_password(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 20
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "SecurePass123!"
        hashed = PasswordManager.hash_password(password)
        
        assert PasswordManager.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "SecurePass123!"
        wrong_password = "WrongPass456!"
        hashed = PasswordManager.hash_password(password)
        
        assert PasswordManager.verify_password(wrong_password, hashed) is False
    
    def test_validate_password_strength_valid(self):
        """Test password strength validation with valid password"""
        password = "MySecurePass123!"
        is_valid, error = PasswordManager.validate_password_strength(password)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_password_strength_too_short(self):
        """Test password strength validation with short password"""
        password = "Short1!"
        is_valid, error = PasswordManager.validate_password_strength(password)
        
        assert is_valid is False
        assert "at least" in error
    
    def test_validate_password_strength_no_uppercase(self):
        """Test password strength validation without uppercase"""
        password = "securepass123!"
        is_valid, error = PasswordManager.validate_password_strength(password)
        
        assert is_valid is False
        assert "uppercase" in error
    
    def test_validate_password_strength_no_digit(self):
        """Test password strength validation without digit"""
        password = "SecurePass!"
        is_valid, error = PasswordManager.validate_password_strength(password)
        
        assert is_valid is False
        assert "digit" in error
    
    def test_validate_password_strength_no_special(self):
        """Test password strength validation without special character"""
        password = "SecurePass123"
        is_valid, error = PasswordManager.validate_password_strength(password)
        
        assert is_valid is False
        assert "special" in error
    
    def test_generate_secure_password(self):
        """Test secure password generation"""
        password = PasswordManager.generate_secure_password(16)
        
        assert len(password) >= 12
        # Verify it meets strength requirements
        is_valid, _ = PasswordManager.validate_password_strength(password)
        assert is_valid is True


class TestJWTManager:
    """Tests for JWT token management"""
    
    def test_create_token(self):
        """Test JWT token creation"""
        payload = {"user_id": "test_user", "role": "admin"}
        token = JWTManager.create_token(payload)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20
    
    def test_verify_token_valid(self):
        """Test verification of valid token"""
        payload = {"user_id": "test_user", "role": "admin"}
        token = JWTManager.create_token(payload)
        
        is_valid, decoded = JWTManager.verify_token(token)
        
        assert is_valid is True
        assert decoded["user_id"] == "test_user"
        assert decoded["role"] == "admin"
    
    def test_verify_token_expired(self):
        """Test verification of expired token"""
        payload = {"user_id": "test_user"}
        # Create token with 0 expiry (already expired)
        token = JWTManager.create_token(payload, expiry_seconds=-1)
        
        is_valid, decoded = JWTManager.verify_token(token)
        
        assert is_valid is False
        assert decoded is None
    
    def test_verify_token_invalid(self):
        """Test verification of invalid token"""
        is_valid, decoded = JWTManager.verify_token("invalid.token.here")
        
        assert is_valid is False
        assert decoded is None
    
    def test_create_user_token(self):
        """Test user authentication token creation"""
        token = JWTManager.create_user_token("user123", "test@example.com", "admin")
        
        is_valid, decoded = JWTManager.verify_token(token)
        assert is_valid is True
        assert decoded["sub"] == "user123"
        assert decoded["email"] == "test@example.com"
        assert decoded["role"] == "admin"
    
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        token = JWTManager.create_refresh_token("user123")
        
        is_valid, decoded = JWTManager.verify_token(token)
        assert is_valid is True
        assert decoded["sub"] == "user123"
        assert decoded["type"] == "refresh"
    
    def test_get_user_from_token(self):
        """Test extracting user ID from token"""
        token = JWTManager.create_user_token("user123", "test@example.com")
        user_id = JWTManager.get_user_from_token(token)
        
        assert user_id == "user123"


class TestOTPManager:
    """Tests for One-Time Password management"""
    
    def test_generate_otp(self):
        """Test OTP generation"""
        otp = OTPManager.generate_otp()
        
        assert len(otp) == 6
        assert otp.isdigit()
    
    def test_generate_hotp(self):
        """Test HMAC-based OTP generation"""
        secret = "BASE32SECRET123"
        otp1 = OTPManager.generate_hotp(secret, 1)
        otp2 = OTPManager.generate_hotp(secret, 1)
        otp3 = OTPManager.generate_hotp(secret, 2)
        
        # Same counter should produce same OTP
        assert otp1 == otp2
        # Different counter should produce different OTP
        assert otp1 != otp3
        assert len(otp1) == 6
        assert otp1.isdigit()
    
    @pytest.mark.asyncio
    async def test_send_verification_otp(self):
        """Test sending verification OTP"""
        with patch('services.email_sender.EmailSender.send_email', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = "email_123"
            
            otp = await OTPManager.send_verification_otp("test@example.com", "verify")
            
            assert len(otp) == 6
            assert otp.isdigit()
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_otp_valid(self):
        """Test OTP verification with valid code"""
        email = "test@example.com"
        
        # First send OTP (this stores it)
        otp = await OTPManager.send_verification_otp(email, "verify")
        
        # Then verify
        is_valid, error = await OTPManager.verify_otp(email, otp, "verify")
        
        assert is_valid is True
        assert error is None
    
    @pytest.mark.asyncio
    async def test_verify_otp_invalid(self):
        """Test OTP verification with invalid code"""
        email = "test@example.com"
        await OTPManager.send_verification_otp(email, "verify")
        
        is_valid, error = await OTPManager.verify_otp(email, "000000", "verify")
        
        assert is_valid is False
        assert "Invalid" in error
    
    @pytest.mark.asyncio
    async def test_generate_password_reset_token(self):
        """Test password reset token generation"""
        token = await OTPManager.generate_password_reset_token("user123")
        
        assert token is not None
        assert len(token) > 20
    
    @pytest.mark.asyncio
    async def test_verify_password_reset_token_valid(self):
        """Test password reset token verification with valid token"""
        user_id = "user123"
        token = await OTPManager.generate_password_reset_token(user_id)
        
        is_valid = await OTPManager.verify_password_reset_token(user_id, token)
        
        assert is_valid is True


class TestTwoFactorAuth:
    """Tests for Two-Factor Authentication"""
    
    def test_generate_secret(self):
        """Test TOTP secret generation"""
        result = TwoFactorAuth.generate_secret("user@example.com")
        
        assert "secret" in result
        assert "provisioning_uri" in result
        assert len(result["secret"]) > 10
        assert "otpauth://" in result["provisioning_uri"]
    
    def test_verify_totp(self):
        """Test TOTP code verification"""
        # Generate secret
        secret = TwoFactorAuth.generate_secret("test@example.com")["secret"]
        
        # Generate valid code
        import pyotp
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()
        
        # Verify
        assert TwoFactorAuth.verify_totp(secret, valid_code) is True
        assert TwoFactorAuth.verify_totp(secret, "000000") is False
    
    def test_generate_backup_codes(self):
        """Test backup code generation"""
        codes = TwoFactorAuth.generate_backup_codes()
        
        assert len(codes) == 10
        for code in codes:
            assert len(code) == 8
            assert code.isalnum()
            assert code.isupper()
    
    @pytest.mark.asyncio
    async def test_enable_disable_2fa(self):
        """Test enabling and disabling 2FA"""
        with patch('core.supabase_client.supabase.table') as mock_table:
            mock_insert = AsyncMock()
            mock_update = AsyncMock()
            mock_table.return_value.insert = mock_insert
            mock_table.return_value.update = mock_update
            
            secret = "BASE32SECRET123"
            codes = ["CODE1234", "CODE5678"]
            
            result = await TwoFactorAuth.enable_2fa("user123", secret, codes)
            assert result is True
            mock_insert.assert_called_once()
            
            result = await TwoFactorAuth.disable_2fa("user123")
            assert result is True
            mock_update.assert_called_once()


class TestSessionManager:
    """Tests for session management"""
    
    def test_create_tokens(self):
        """Test token creation"""
        with patch('core.redis_client.redis_client.setex') as mock_redis:
            mock_redis.return_value = True
            
            tokens = SessionManager.create_tokens("user123", {"device": "test"})
            
            assert "access_token" in tokens
            assert "refresh_token" in tokens
            assert "token_type" in tokens
            assert tokens["token_type"] == "bearer"
            assert tokens["expires_in"] > 0
    
    def test_verify_access_token_valid(self):
        """Test access token verification"""
        tokens = SessionManager.create_tokens("user123")
        
        is_valid, payload = SessionManager.verify_access_token(tokens["access_token"])
        
        assert is_valid is True
        assert payload["sub"] == "user123"
    
    def test_verify_access_token_invalid(self):
        """Test access token verification with invalid token"""
        is_valid, payload = SessionManager.verify_access_token("invalid.token")
        
        assert is_valid is False
        assert payload is None
    
    def test_refresh_access_token(self):
        """Test refreshing access token"""
        tokens = SessionManager.create_tokens("user123")
        
        success, new_tokens = SessionManager.refresh_access_token(tokens["refresh_token"])
        
        assert success is True
        assert new_tokens is not None
        assert "access_token" in new_tokens
    
    @pytest.mark.asyncio
    async def test_revoke_session(self):
        """Test session revocation"""
        with patch('core.redis_client.redis_client.delete') as mock_redis:
            mock_redis.return_value = 1
            
            with patch('core.supabase_client.supabase.table') as mock_supabase:
                mock_update = AsyncMock()
                mock_table = Mock()
                mock_table.update.return_value = mock_update
                mock_supabase.return_value = mock_table
                
                result = await SessionManager.revoke_session("session_123")
                
                assert result is True
                mock_redis.assert_called_once()
