"""
Unit Tests - Core Services
Testing TruthEngine, CentPay, AI Shrinker services
Version: 31.0
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from services.truth_engine import TruthEngine
from services.centpay_ledger import CentPayLedger
from services.ai_shrinker import AIShrinker
from services.compliance_shield import ComplianceShield


class TestTruthEngine:
    """Tests for TruthEngine service"""
    
    @pytest.mark.asyncio
    async def test_verify_truthful_statement(self):
        """Test verification of truthful statement"""
        result = await TruthEngine.verify(
            text="The Earth revolves around the Sun.",
            user_id="test_user",
            job_id="job_123"
        )
        
        assert "verdict" in result
        assert "confidence" in result
        assert result["verdict"] in ["VERIFIED_TRUE", "VERIFIED_FALSE", "OPINION_DETECTED"]
        assert 0 <= result["confidence"] <= 100
    
    @pytest.mark.asyncio
    async def test_verify_empty_text(self):
        """Test verification with empty text"""
        result = await TruthEngine.verify(
            text="",
            user_id="test_user",
            job_id="job_123"
        )
        
        assert result["verdict"] == "INSUFFICIENT_DATA"
        assert result["confidence"] == 0.0
    
    @pytest.mark.asyncio
    async def test_verify_short_text(self):
        """Test verification with very short text"""
        result = await TruthEngine.verify(
            text="Hi",
            user_id="test_user",
            job_id="job_123"
        )
        
        assert result["verdict"] == "INSUFFICIENT_DATA"
    
    @pytest.mark.asyncio
    async def test_cache_hit(self):
        """Test cache functionality"""
        text = "The sky is blue on Earth."
        
        # First call - should compute
        result1 = await TruthEngine.verify(text, "test_user", "job_1")
        
        # Second call - should hit cache
        result2 = await TruthEngine.verify(text, "test_user", "job_2")
        
        assert result1["verdict"] == result2["verdict"]
        assert result2.get("cached", False) is True
    
    @pytest.mark.asyncio
    async def test_clear_cache(self):
        """Test cache clearing"""
        text = "Test statement for cache clearing."
        
        await TruthEngine.verify(text, "test_user", "job_1")
        TruthEngine.clear_cache()
        
        # Should recompute after cache clear
        result = await TruthEngine.verify(text, "test_user", "job_2")
        assert result.get("cached", False) is False


class TestCentPayLedger:
    """Tests for CentPay ledger service"""
    
    @pytest.mark.asyncio
    async def test_process_charge_usd(self):
        """Test processing USD charge"""
        result = await CentPayLedger.process_charge(
            user_id="user_123",
            merchant_id="merchant_456",
            fiat_amount=10.00,
            currency_code="USD"
        )
        
        assert "amount_usd" in result
        assert "cashback" in result
        assert result["amount_usd"] <= 10.00  # After cashback deduction
        assert result["currency"] == "USD"
    
    @pytest.mark.asyncio
    async def test_process_charge_tzs(self):
        """Test processing TZS charge"""
        result = await CentPayLedger.process_charge(
            user_id="user_123",
            merchant_id="merchant_456",
            fiat_amount=5000.00,
            currency_code="TZS"
        )
        
        assert "amount_usd" in result
        assert result["amount_usd"] > 0
        assert result["amount_usd"] < 5000
        assert result["currency"] == "TZS"
    
    @pytest.mark.asyncio
    async def test_process_charge_invalid_currency(self):
        """Test processing with invalid currency"""
        result = await CentPayLedger.process_charge(
            user_id="user_123",
            merchant_id="merchant_456",
            fiat_amount=100.00,
            currency_code="INVALID"
        )
        
        # Should fall back to USD rate of 1.0
        assert "amount_usd" in result
        assert result["amount_usd"] > 0
    
    @pytest.mark.asyncio
    async def test_process_charge_zero_amount(self):
        """Test processing zero amount (should fail)"""
        with pytest.raises(Exception):
            await CentPayLedger.process_charge(
                user_id="user_123",
                merchant_id="merchant_456",
                fiat_amount=0,
                currency_code="USD"
            )
    
    @pytest.mark.asyncio
    async def test_get_balance(self):
        """Test getting user balance"""
        with patch('core.supabase_client.supabase.table') as mock_table:
            mock_select = Mock()
            mock_select.execute = Mock()
            mock_select.execute.return_value.data = [{"balance_usd": 100.50}]
            mock_table.return_value.select.return_value = mock_select
            
            balance = await CentPayLedger.get_balance("user_123")
            
            assert "balance_usd" in balance
            assert balance["balance_usd"] == 100.50
    
    @pytest.mark.asyncio
    async def test_credit_wallet(self):
        """Test crediting wallet"""
        with patch('core.supabase_client.supabase.table') as mock_table:
            mock_select = Mock()
            mock_select.execute = Mock()
            mock_select.execute.return_value.data = [{"balance_usd": 100.00}]
            mock_table.return_value.select.return_value = mock_select
            
            mock_update = AsyncMock()
            mock_table.return_value.update.return_value = mock_update
            
            result = await CentPayLedger.credit_wallet("user_123", 50.00, "refund")
            
            assert result is True


class TestAIShrinker:
    """Tests for AI Shrinker service"""
    
    @pytest.mark.asyncio
    async def test_start_batch_compression(self):
        """Test starting batch compression"""
        with patch('core.supabase_client.supabase.table') as mock_table:
            mock_insert = AsyncMock()
            mock_table.return_value.insert = mock_insert
            
            batch_id = await AIShrinker.start_batch_compression(
                user_id="user_123",
                models=[
                    {"model_repo_url": "meta-llama/Llama-3-70B", "target_precision": "int4"},
                    {"model_repo_url": "mistralai/Mistral-7B", "target_precision": "int4"}
                ]
            )
            
            assert batch_id is not None
            assert len(batch_id) > 0
            mock_insert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_job_status(self):
        """Test getting job status"""
        with patch('core.supabase_client.supabase.table') as mock_table:
            mock_select = Mock()
            mock_select.execute = Mock()
            mock_select.execute.return_value.data = [{
                "job_id": "job_123",
                "job_status": "completed",
                "compressed_size_gb": 14.0
            }]
            mock_table.return_value.select.return_value = mock_select
            
            status = await AIShrinker.get_job_status("job_123")
            
            assert status is not None
            assert status["job_status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_get_batch_status(self):
        """Test getting batch status"""
        with patch('core.supabase_client.supabase.table') as mock_table:
            # Mock batch query
            mock_batch = Mock()
            mock_batch.execute = Mock()
            mock_batch.execute.return_value.data = [{"batch_id": "batch_123", "status": "processing"}]
            
            # Mock jobs query
            mock_jobs = Mock()
            mock_jobs.execute = Mock()
            mock_jobs.execute.return_value.data = [{"job_id": "job_1"}, {"job_id": "job_2"}]
            
            mock_table.return_value.select.side_effect = [mock_batch, mock_jobs]
            
            status = await AIShrinker.get_batch_status("batch_123")
            
            assert status is not None
            assert "batch" in status
            assert "jobs" in status
            assert status["total_jobs"] == 2


class TestComplianceShield:
    """Tests for Compliance Shield service"""
    
    def test_scan_pii_email(self):
        """Test scanning for email PII"""
        text = "Contact me at user@example.com for more info."
        detections = ComplianceShield.scan(text)
        
        email_detections = [d for d in detections if d.type == "email"]
        assert len(email_detections) >= 1
        assert email_detections[0].value == "user@example.com"
    
    def test_scan_pii_credit_card(self):
        """Test scanning for credit card PII"""
        text = "My card number is 4111-2222-3333-4444."
        detections = ComplianceShield.scan(text)
        
        card_detections = [d for d in detections if d.type == "credit_card"]
        assert len(card_detections) >= 1
    
    def test_redact_email(self):
        """Test email redaction"""
        text = "Email: user@example.com"
        redacted = ComplianceShield.redact(text)
        
        assert "user@example.com" not in redacted
        assert "[REDACTED_EMAIL]" in redacted
    
    def test_redact_credit_card(self):
        """Test credit card redaction"""
        text = "Card: 4111222233334444"
        redacted = ComplianceShield.redact(text)
        
        assert "4111222233334444" not in redacted
        assert "[REDACTED_CARD]" in redacted
    
    def test_has_pii_true(self):
        """Test PII detection returns True when PII present"""
        text = "Email: user@example.com"
        assert ComplianceShield.has_pii(text) is True
    
    def test_has_pii_false(self):
        """Test PII detection returns False when no PII"""
        text = "This is a normal sentence without any personal information."
        assert ComplianceShield.has_pii(text) is False
    
    def test_get_risk_score(self):
        """Test risk score calculation"""
        text = "Email: user@example.com, Card: 4111222233334444"
        risk = ComplianceShield.get_risk_score(text)
        
        assert "has_pii" in risk
        assert risk["has_pii"] is True
        assert "risk_score" in risk
        assert risk["risk_score"] > 0
        assert "detection_count" in risk
        assert risk["detection_count"] >= 2
