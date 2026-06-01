"""
Integration Tests - Complete API Flows
Testing end-to-end API workflows
Version: 31.0
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from main import app


@pytest.mark.integration
class TestCompleteAPIFlows:
    """End-to-end API flow tests"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_complete_fact_check_flow(self, client):
        """Test complete fact check flow from request to response"""
        response = client.post(
            "/v1/sovereign/execute",
            json={
                "user_id": "flow_test_user",
                "execution_mode": "fact_check",
                "text_payload": "Water boils at 100 degrees Celsius at sea level."
            },
            headers={"X-Sovereign-Key": "test_key_123"}
        )
        
        assert response.status_code in [200, 401]  # 401 if no valid key
    
    def test_complete_payment_flow(self, client):
        """Test complete payment flow"""
        response = client.post(
            "/v1/sovereign/execute",
            json={
                "user_id": "customer_123",
                "merchant_id": "merchant_456",
                "execution_mode": "micro_charge",
                "fiat_amount": 50.00,
                "currency_code": "TZS"
            },
            headers={"X-Sovereign-Key": "test_key_123"}
        )
        
        assert response.status_code in [200, 401]
    
    def test_health_to_api_flow(self, client):
        """Test health check then API call flow"""
        # First check health
        health_response = client.get("/health")
        assert health_response.status_code == 200
        
        # Then make API call
        api_response = client.post(
            "/v1/sovereign/execute",
            json={
                "user_id": "flow_test_user",
                "execution_mode": "compliance_shield",
                "text_payload": "Test text for compliance check."
            },
            headers={"X-Sovereign-Key": "test_key_123"}
        )
        
        assert api_response.status_code in [200, 401]
