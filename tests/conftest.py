"""
Pytest Configuration - Shared Fixtures and Hooks
For test configuration and common test utilities
Version: 31.0
"""

import pytest
import asyncio
from typing import Generator
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator:
    """Create test client for FastAPI app"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing"""
    with patch('core.supabase_client.supabase') as mock:
        mock.table.return_value.select.return_value.execute.return_value.data = []
        mock.table.return_value.insert.return_value.execute.return_value.data = []
        mock.table.return_value.update.return_value.execute.return_value.data = []
        yield mock


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    with patch('core.redis_client.redis_client') as mock:
        mock.get.return_value = None
        mock.set.return_value = True
        mock.delete.return_value = 1
        yield mock


@pytest.fixture
def sample_api_key():
    """Sample API key for testing"""
    return "sk_sov_test_1234567890abcdef"


@pytest.fixture
def sample_fact_check_payload():
    """Sample fact check payload"""
    return {
        "user_id": "test_user",
        "execution_mode": "fact_check",
        "text_payload": "The Earth revolves around the Sun."
    }


@pytest.fixture
def sample_payment_payload():
    """Sample payment payload"""
    return {
        "user_id": "test_user",
        "merchant_id": "test_merchant",
        "execution_mode": "micro_charge",
        "fiat_amount": 50.00,
        "currency_code": "TZS"
    }


@pytest.fixture
def sample_compression_payload():
    """Sample model compression payload"""
    return {
        "user_id": "test_user",
        "execution_mode": "bulk_compress",
        "bulk_models": [
            {"model_repo_url": "meta-llama/Llama-3-70B", "target_precision": "int4"}
        ]
    }


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security test"
    )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests by default"""
    if not config.getoption("-k") and not config.getoption("-m"):
        skip_integration = pytest.mark.skip(reason="Use -m integration to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
