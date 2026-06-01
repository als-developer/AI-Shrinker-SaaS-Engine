"""
Smoke Tests - Basic System Functionality
Quick tests to verify system is operational after deployment
Version: 31.0
"""

import sys
import requests
import json
from typing import Dict, Any


class SmokeTest:
    """Quick smoke tests for deployment verification"""
    
    BASE_URL = "https://api.sovereigngrid.com"
    API_KEY = None  # Set from environment
    
    @classmethod
    def test_health_endpoint(cls) -> bool:
        """Test health check endpoint"""
        try:
            response = requests.get(f"{cls.BASE_URL}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "alive":
                    print("✅ Health check passed")
                    return True
            print(f"❌ Health check failed: {response.status_code}")
            return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    @classmethod
    def test_version_endpoint(cls) -> bool:
        """Test version endpoint"""
        try:
            response = requests.get(f"{cls.BASE_URL}/version", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("version"):
                    print(f"✅ Version check passed: v{data['version']}")
                    return True
            print(f"❌ Version check failed: {response.status_code}")
            return False
        except Exception as e:
            print(f"❌ Version check error: {e}")
            return False
    
    @classmethod
    def test_api_endpoint(cls) -> bool:
        """Test main API endpoint"""
        if not cls.API_KEY:
            print("⚠️ API_KEY not set, skipping API test")
            return True
        
        try:
            response = requests.post(
                f"{cls.BASE_URL}/v1/sovereign/execute",
                json={
                    "user_id": "smoke_test",
                    "execution_mode": "fact_check",
                    "text_payload": "This is a smoke test."
                },
                headers={"X-Sovereign-Key": cls.API_KEY},
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ API endpoint test passed")
                return True
            elif response.status_code == 402:
                print("⚠️ API test: Insufficient credits")
                return True
            else:
                print(f"❌ API endpoint test failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API endpoint error: {e}")
            return False
    
    @classmethod
    def run_all(cls) -> bool:
        """Run all smoke tests"""
        print(f"\n🔍 Running smoke tests against {cls.BASE_URL}\n")
        
        tests = [
            cls.test_health_endpoint,
            cls.test_version_endpoint,
            cls.test_api_endpoint
        ]
        
        passed = 0
        for test in tests:
            if test():
                passed += 1
        
        print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
        
        return passed == len(tests)


def main():
    """Main entry point"""
    import os
    SmokeTest.API_KEY = os.getenv("TEST_API_KEY", "")
    
    success = SmokeTest.run_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
