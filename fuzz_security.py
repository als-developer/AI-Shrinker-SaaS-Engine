"""
Fuzz Security - Automated Security Penetration Testing
Continuous security scanning and vulnerability detection
Version: 31.0
"""

import asyncio
import json
import random
from typing import Dict, Any, List
import httpx
import logging

logger = logging.getLogger(__name__)


class SecurityFuzzer:
    """Automated security fuzzing for API endpoints"""
    
    # Test payloads for different attack vectors
    ATTACK_PAYLOADS = {
        "sql_injection": [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "1' UNION SELECT * FROM users --",
            "admin'--",
            "' OR 1=1; --"
        ],
        "xss": [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert('XSS')",
            "<svg onload=alert(1)>",
            "'; alert('XSS'); //"
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\win.ini",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2f",
            "....//....//....//etc/passwd"
        ],
        "command_injection": [
            "; ls -la",
            "| cat /etc/passwd",
            "$(whoami)",
            "`id`",
            "&& ping -c 10 127.0.0.1"
        ],
        "noSQL_injection": [
            '{"$ne": null}',
            '{"$gt": ""}',
            '{"$regex": ".*"}',
            '{"$or": []}'
        ],
        "large_payload": [
            "A" * 10000,
            "B" * 50000,
            {"data": "x" * 100000}
        ],
        "invalid_json": [
            "{invalid json}",
            "{'single': 'quotes'}",
            "not json at all",
            "{\"unclosed\": \"quote}"
        ]
    }
    
    @classmethod
    async def run_full_scan(cls, base_url: str, api_key: str) -> Dict[str, Any]:
        """
        Run full security scan against all endpoints
        
        Args:
            base_url: API base URL
            api_key: API key for authentication
            
        Returns:
            Scan results
        """
        logger.info(f"Starting security scan against {base_url}")
        
        endpoints = [
            "/v1/sovereign/execute",
            "/health",
            "/ready"
        ]
        
        results = {
            "scan_id": f"scan_{asyncio.get_event_loop().time()}",
            "target": base_url,
            "start_time": asyncio.get_event_loop().time(),
            "endpoints": {},
            "summary": {
                "total_tests": 0,
                "vulnerabilities_found": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            for endpoint in endpoints:
                endpoint_results = await cls._test_endpoint(
                    client, base_url, endpoint, api_key
                )
                results["endpoints"][endpoint] = endpoint_results
                
                for vuln in endpoint_results.get("vulnerabilities", []):
                    results["summary"]["vulnerabilities_found"] += 1
                    results["summary"][vuln.get("severity", "low")] += 1
                
                results["summary"]["total_tests"] += endpoint_results.get("tests_run", 0)
        
        results["end_time"] = asyncio.get_event_loop().time()
        results["duration_seconds"] = results["end_time"] - results["start_time"]
        
        logger.info(f"Scan complete. Found {results['summary']['vulnerabilities_found']} issues")
        
        return results
    
    @classmethod
    async def _test_endpoint(
        cls,
        client: httpx.AsyncClient,
        base_url: str,
        endpoint: str,
        api_key: str
    ) -> Dict[str, Any]:
        """Test a single endpoint with all attack vectors"""
        
        full_url = f"{base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "X-Sovereign-Key": api_key
        }
        
        results = {
            "endpoint": endpoint,
            "tests_run": 0,
            "vulnerabilities": []
        }
        
        for attack_type, payloads in cls.ATTACK_PAYLOADS.items():
            for payload in payloads:
                test_result = await cls._send_test_request(
                    client, full_url, headers, attack_type, payload
                )
                
                results["tests_run"] += 1
                
                if test_result.get("vulnerable"):
                    results["vulnerabilities"].append({
                        "type": attack_type,
                        "payload": str(payload)[:100],
                        "severity": test_result.get("severity", "medium"),
                        "status_code": test_result.get("status_code"),
                        "response_preview": test_result.get("response_preview", "")[:200]
                    })
        
        return results
    
    @classmethod
    async def _send_test_request(
        cls,
        client: httpx.AsyncClient,
        url: str,
        headers: Dict,
        attack_type: str,
        payload: Any
    ) -> Dict[str, Any]:
        """Send a single test request"""
        
        # Prepare test body
        test_body = {
            "user_id": "security_test",
            "execution_mode": "fact_check",
            "text_payload": str(payload) if isinstance(payload, str) else json.dumps(payload)
        }
        
        try:
            response = await client.post(url, json=test_body, headers=headers)
            
            # Check for vulnerability indicators
            vulnerable = False
            severity = "low"
            
            # SQL injection indicators
            if attack_type == "sql_injection":
                if any(indicator in response.text.lower() for indicator in ["sql", "mysql", "syntax", "error", "database"]):
                    vulnerable = True
                    severity = "critical"
            
            # XSS indicators
            elif attack_type == "xss":
                if str(payload) in response.text:
                    vulnerable = True
                    severity = "high"
            
            # Path traversal indicators
            elif attack_type == "path_traversal":
                if any(indicator in response.text for indicator in ["root:", "bin/bash", "drivers", "etc/passwd"]):
                    vulnerable = True
                    severity = "high"
            
            # Command injection indicators
            elif attack_type == "command_injection":
                if any(indicator in response.text for indicator in ["uid=", "gid=", "groups=", "ping"]):
                    vulnerable = True
                    severity = "critical"
            
            # Large payload - check for proper handling
            elif attack_type == "large_payload" and response.status_code == 413:
                vulnerable = False  # Properly rejected
            
            return {
                "vulnerable": vulnerable,
                "severity": severity if vulnerable else None,
                "status_code": response.status_code,
                "response_preview": response.text[:200] if vulnerable else None
            }
            
        except httpx.TimeoutException:
            return {"vulnerable": False, "error": "timeout"}
        except Exception as e:
            return {"vulnerable": False, "error": str(e)}
