"""
Stress Test - High-Volume Load Testing Suite
Simulates millions of concurrent requests to test system limits
Version: 31.0
"""

import asyncio
import json
import time
import random
from typing import Dict, Any, List
import httpx
import logging

logger = logging.getLogger(__name__)


class StressTester:
    """High-volume load testing for API endpoints"""
    
    @classmethod
    async def run_load_test(
        cls,
        base_url: str,
        api_key: str,
        total_requests: int = 10000,
        concurrency: int = 100
    ) -> Dict[str, Any]:
        """
        Run load test with specified parameters
        
        Args:
            base_url: API base URL
            api_key: API key for authentication
            total_requests: Total number of requests to send
            concurrency: Number of concurrent workers
            
        Returns:
            Performance metrics
        """
        logger.info(f"Starting load test: {total_requests} requests, {concurrency} concurrent")
        
        start_time = time.perf_counter()
        
        # Create queue of requests
        request_queue = asyncio.Queue()
        for i in range(total_requests):
            await request_queue.put(i)
        
        # Track results
        results = {
            "success": 0,
            "failed": 0,
            "latencies": [],
            "errors": []
        }
        
        # Create workers
        async with httpx.AsyncClient(timeout=10.0) as client:
            workers = [
                cls._worker(
                    client, base_url, api_key, request_queue, results
                )
                for _ in range(concurrency)
            ]
            
            await asyncio.gather(*workers)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Calculate statistics
        latencies = results["latencies"]
        latencies.sort()
        
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        p50_latency = latencies[int(len(latencies) * 0.5)] if latencies else 0
        p90_latency = latencies[int(len(latencies) * 0.9)] if latencies else 0
        p99_latency = latencies[int(len(latencies) * 0.99)] if latencies else 0
        
        report = {
            "test_id": f"load_{int(time.time())}",
            "total_requests": total_requests,
            "concurrency": concurrency,
            "successful": results["success"],
            "failed": results["failed"],
            "success_rate": (results["success"] / total_requests) * 100,
            "total_time_seconds": round(total_time, 2),
            "requests_per_second": round(total_requests / total_time, 2),
            "latency_ms": {
                "avg": round(avg_latency, 2),
                "p50": round(p50_latency, 2),
                "p90": round(p90_latency, 2),
                "p99": round(p99_latency, 2),
                "min": round(min(latencies), 2) if latencies else 0,
                "max": round(max(latencies), 2) if latencies else 0
            }
        }
        
        logger.info(f"Load test complete: {report['requests_per_second']} req/sec")
        
        return report
    
    @classmethod
    async def _worker(
        cls,
        client: httpx.AsyncClient,
        base_url: str,
        api_key: str,
        queue: asyncio.Queue,
        results: Dict
    ):
        """Worker that processes requests from queue"""
        
        modes = ["fact_check", "micro_charge", "compliance_shield"]
        
        while not queue.empty():
            try:
                _ = queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            
            try:
                # Prepare request
                mode = random.choice(modes)
                
                payload = {
                    "user_id": f"load_test_{random.randint(1, 1000)}",
                    "execution_mode": mode,
                    "text_payload": "This is a load test request to measure system performance under stress.",
                    "fiat_amount": 50.00 if mode == "micro_charge" else 0.0,
                    "currency_code": "TZS"
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "X-Sovereign-Key": api_key
                }
                
                # Send request with timing
                start = time.perf_counter() * 1000
                response = await client.post(
                    f"{base_url}/v1/sovereign/execute",
                    json=payload,
                    headers=headers
                )
                end = time.perf_counter() * 1000
                latency = end - start
                
                if response.status_code == 200:
                    results["success"] += 1
                    results["latencies"].append(latency)
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "status": response.status_code,
                        "body": response.text[:100]
                    })
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"error": str(e)})
            
            queue.task_done()
