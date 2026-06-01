"""
Performance Benchmarks - API Load Testing
Benchmarking API performance under load
Version: 31.0
"""

import asyncio
import time
import json
from typing import Dict, Any, List
import aiohttp
import statistics


class APIBenchmark:
    """Performance benchmarking for API endpoints"""
    
    BASE_URL = "http://localhost:8000"
    API_KEY = "test_benchmark_key"
    
    @classmethod
    async def benchmark_endpoint(
        cls,
        endpoint: str,
        payload: Dict,
        iterations: int = 100,
        concurrency: int = 10
    ) -> Dict[str, Any]:
        """
        Benchmark an API endpoint
        
        Args:
            endpoint: API endpoint path
            payload: Request payload
            iterations: Number of requests
            concurrency: Number of concurrent requests
        
        Returns:
            Benchmark results
        """
        latencies = []
        errors = 0
        successful = 0
        
        async def make_request(session, semaphore):
            nonlocal errors, successful
            async with semaphore:
                start = time.perf_counter()
                try:
                    async with session.post(
                        f"{cls.BASE_URL}{endpoint}",
                        json=payload,
                        headers={"X-Sovereign-Key": cls.API_KEY}
                    ) as response:
                        latency = (time.perf_counter() - start) * 1000
                        latencies.append(latency)
                        
                        if response.status == 200:
                            successful += 1
                        else:
                            errors += 1
                except Exception:
                    errors += 1
        
        semaphore = asyncio.Semaphore(concurrency)
        
        async with aiohttp.ClientSession() as session:
            tasks = [make_request(session, semaphore) for _ in range(iterations)]
            await asyncio.gather(*tasks)
        
        if latencies:
            latencies.sort()
            return {
                "endpoint": endpoint,
                "total_requests": iterations,
                "successful": successful,
                "errors": errors,
                "success_rate": (successful / iterations) * 100,
                "latency_ms": {
                    "min": min(latencies),
                    "max": max(latencies),
                    "avg": statistics.mean(latencies),
                    "p50": latencies[int(len(latencies) * 0.5)],
                    "p90": latencies[int(len(latencies) * 0.9)],
                    "p95": latencies[int(len(latencies) * 0.95)],
                    "p99": latencies[int(len(latencies) * 0.99)]
                }
            }
        
        return {
            "endpoint": endpoint,
            "total_requests": iterations,
            "successful": 0,
            "errors": iterations,
            "success_rate": 0,
            "latency_ms": {}
        }
    
    @classmethod
    async def run_full_benchmark(cls) -> Dict[str, Any]:
        """Run benchmark on all critical endpoints"""
        endpoints = [
            ("/v1/sovereign/execute", {
                "user_id": "benchmark_user",
                "execution_mode": "fact_check",
                "text_payload": "Benchmark test text."
            }),
            ("/health", {}),
            ("/version", {})
        ]
        
        results = {}
        for endpoint, payload in endpoints:
            print(f"Benchmarking {endpoint}...")
            results[endpoint] = await cls.benchmark_endpoint(endpoint, payload)
        
        return results


async def main():
    """Run benchmarks"""
    results = await APIBenchmark.run_full_benchmark()
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
