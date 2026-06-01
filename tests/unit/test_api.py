"""
Unit Tests - API Endpoints
Testing FastAPI routes, request validation, and responses
Version: 31.0
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock, patch
import json

from main import app
from core.auth import authenticate_developer
from core.rate_limiter import enforce_rate_limit


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_auth():
    """Mock authentication dependency"""
    async def mock_auth():
        return "test_developer"
    
    app.dependency_overrides[authenticate_developer] = mock_auth
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_rate_limit():
    """Mock rate limit dependency"""
    async def mock_rate_limit():
        return {"client_id": "test_client", "limit": 100, "remaining": 99}
    
    app.dependency_overrides[enforce_rate_limit] = mock_rate_limit
    yield
    app.dependency_overrides.clear()


class TestHealthEndpoints:
    """Tests for health check endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "alive"
    
    def test_readiness_check(self, client):
        """Test readiness check endpoint"""
        response = client.get("/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_version_endpoint(self, client):
        """Test version endpoint"""
        response = client.get("/version")
        
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert data["version"] == "31.0"


class TestSovereignAPI:
    """Tests for main sovereign API endpoint"""
    
    @patch('services.truth_engine.TruthEngine.verify')
    def test_fact_check_success(self, mock_verify, client, mock_auth, mock_rate_limit):
        """Test fact_check execution mode"""
        mock_verify.return_value = {
            "verdict": "VERIFIED_TRUE",
            "confidence": 98.5,
            "sources": [{"title": "Source 1"}]
        }
        
        response = client.post(
            "/v1/sovereign/execute",
            json={
                "user_id": "test_user",
                "execution_mode": "fact_check",
                "text_payload": "The Earth revolves around the Sun."
            },
            headers={"X-Sovereign-Key": "test_key"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "verdict" in data
        assert data["verdict"] == "VERIFIED_TRUE"
    
    @patch('services.centpay_ledger.CentPayLedger.process_charge')
    def test_micro_charge_success(self, mock_charge, client, mock_auth, mock_rate_limit):
        """Test micro_charge execution mode"""
        mock_charge.return_value = {
            "amount_usd": 0.0191,
            "cashback": 0.50
        }
        
        response = client.post(
            "/v1/sovereign/execute",
            json={
                "user_id": "test_user",
                "merchant_id": "merchant_123",
                "execution_mode": "micro_charge",
                "fiat_amount": 50.00,
                "currency_code": "TZS"
            },
            headers={"X-Sovereign-Key": "test_key"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ledger_settled_locklessly"
        assert "tx_token" in data
    
    @patch('services.ai_shrinker.AIShrinker.start_batch_compression')
    def test_bulk_compress_success(self, mock_compress, client, mock_auth, mock_rate_limit):
        """Test bulk_compress execution mode"""
        mock_compress.return_value = "batch_123"
        
        response = client.post(
            "/v1/sovereign/execute",
            json={
                "user_id": "test_user",
                "execution_mode": "bulk_compress",
                "bulk_models": [
                    {"model_repo_url": "meta-llama/Llama-3-70B", "target_precision": "int4"}
                ]
            },
            headers={"X-Sovereign-Key": "test_key"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "batch_processing_initiated"
        assert "batch_token" in data
    
    def test_compliance_shield_success(self, client, mock_auth, mock_rate_limit):
        """Test compliance_shield execution mode"""
        response = client.post(
            "/v1/sovereign/execute",
            json={
                "user_id": "test_user",
                "execution_mode": "compliance_shield",
                "text_payload": "Contact user@example.com"
            },
            headers={"X-Sovereign-Key": "test_key"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "shield_active"
        assert "secure" in data
    
    def test_invalid_execution_mode(self, client, mock_auth, mock_rate_limit):
        """Test invalid execution mode"""
        response = client.post(
            "/v1/sovereign/execute",
            json={
                "user_id": "test_user",
                "execution_mode": "invalid_mode",
                "text_payload": "test"
            },
            headers={"X-Sovereign-Key": "test_key"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    def test_missing_api_key(self, client):
        """Test missing API key header"""
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


class TestRateLimiting:
    """Tests for rate limiting"""
    
    def test_rate_limit_exceeded(self, client, mock_auth):
        """Test rate limit exceeded response"""
        # Override rate limit to always exceed
        async def mock_rate_limit_exceeded():
            from fastapi import HTTPException
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        app.dependency_overrides[enforce_rate_limit] = mock_rate_limit_exceeded
        
        response = client.post(
            "/v1/sovereign/execute",
            json={
                "user_id": "test_user",
                "execution_mode": "fact_check",
                "text_payload": "test"
            },
            headers={"X-Sovereign-Key": "test_key"}
        )
        
        assert response.status_code == 429
        data = response.json()
        assert "rate limit" in data["detail"].lower()
        
        app.dependency_overrides.clear()
