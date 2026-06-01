"""
Security Tests - Penetration and Vulnerability Testing
Testing security boundaries, injection attacks, and authentication
Version: 31.0
"""

import pytest
from fastapi.testclient import TestClient
import json

from main import app


class TestSecurityBoundaries:
    """Test security boundaries and attack vectors"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_sql_injection_prevention(self, client):
        """Test SQL injection attempts are blocked"""
        injection_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "1' UNION SELECT * FROM users --",
            "admin'--"
        ]
        
        for payload in injection_payloads:
            response = client.post(
                "/v1/sovereign/execute",
                json={
                    "user_id": payload,
                    "execution_mode": "fact_check",
                    "text_payload": "Test"
                },
                headers={"X-Sovereign-Key": "test_key"}
            )
            
            # Should not return database errors
            assert "sql" not in response.text.lower()
            assert "database" not in response.text.lower()
    
    def test_xss_prevention(self, client):
        """Test XSS attempts are sanitized"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert('XSS')"
        ]
        
        for payload in xss_payloads:
            response = client.post(
                "/v1/sovereign/execute",
                json={
                    "user_id": "test_user",
                    "execution_mode": "fact_check",
                    "text_payload": payload
                },
                headers={"X-Sovereign-Key": "test_key"}
            )
            
            # HTML should be escaped, not executed
            assert "<script>" not in response.text or "&lt;script&gt;" in response.text
    
    def test_path_traversal_prevention(self, client):
        """Test path traversal attempts are blocked"""
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\win.ini",
            "%2e%2e%2f%2e%2e%2f"
        ]
        
        for payload in traversal_payloads:
            response = client.post(
                "/v1/sovereign/execute",
                json={
                    "user_id": "test_user",
                    "execution_mode": "fact_check",
                    "text_payload": payload
                },
                headers={"X-Sovereign-Key": "test_key"}
            )
            
            # Should not expose system files
            assert "root:" not in response.text
            assert "bin/bash" not in response.text
    
    def test_large_payload_limit(self, client):
        """Test large payloads are rejected or handled gracefully"""
        large_payload = "A" * 1000000  # 1MB payload
        
        response = client.post(
            "/v1/sovereign/execute",
            json={
                "user_id": "test_user",
                "execution_mode": "fact_check",
                "text_payload": large_payload
            },
            headers={"X-Sovereign-Key": "test_key"}
        )
        
        # Should either handle or reject gracefully
        assert response.status_code != 500
    
    def test_missing_auth_header(self, client):
        """Test requests without auth header are rejected"""
        response = client.post(
            "/v1/sovereign/execute",
            json={
                "user_id": "test_user",
                "execution_mode": "fact_check",
                "text_payload": "test"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_invalid_api_key(self, client):
        """Test invalid API key is rejected"""
        response = client.post(
            "/v1/sovereign/execute",
            json={
                "user_id": "test_user",
                "execution_mode": "fact_check",
                "text_payload": "test"
            },
            headers={"X-Sovereign-Key": "invalid_key_123"}
        )
        
        assert response.status_code == 401 or response.status_code == 403
    
    def test_malformed_json(self, client):
        """Test malformed JSON is rejected"""
        response = client.post(
            "/v1/sovereign/execute",
            data="not valid json",
            headers={"Content-Type": "application/json", "X-Sovereign-Key": "test_key"}
        )
        
        assert response.status_code == 422
    
    def test_negative_amount_payment(self, client):
        """Test negative payment amounts are rejected"""
        response = client.post(
            "/v1/sovereign/execute",
            json={
                "user_id": "test_user",
                "execution_mode": "micro_charge",
                "fiat_amount": -50.00,
                "currency_code": "USD"
            },
            headers={"X-Sovereign-Key": "test_key"}
        )
        
        # Should reject negative amounts
        assert response.status_code in [400, 422]
