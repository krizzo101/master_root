"""
Performance testing script for ACCF Research Agent.

This script provides basic performance testing capabilities to measure
response times and throughput for the API endpoints.
"""

import asyncio
import time
import statistics
import aiohttp
import json
from typing import List
from dataclasses import dataclass


@dataclass
class PerformanceResult:
    """Container for performance test results."""

    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    requests_per_second: float
    error_rate: float


class PerformanceTester:
    """Performance testing utility for ACCF Research Agent."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[PerformanceResult] = []

    async def test_endpoint(
        self, endpoint: str, num_requests: int = 100, concurrent: int = 10
    ) -> PerformanceResult:
        """Test a single endpoint with specified parameters."""
        print(f"Testing endpoint: {endpoint}")
        print(f"Requests: {num_requests}, Concurrent: {concurrent}")

        response_times = []
        successful_requests = 0
        failed_requests = 0
        start_time = time.time()

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(concurrent)

        async def make_request():
            nonlocal successful_requests, failed_requests
            async with semaphore:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.base_url}{endpoint}"
                    request_start = time.time()

                    try:
                        async with session.get(url) as response:
                            response_time = time.time() - request_start
                            response_times.append(response_time)

                            if response.status == 200:
                                successful_requests += 1
                            else:
                                failed_requests += 1

                    except Exception as e:
                        failed_requests += 1
                        print(f"Request failed: {e}")

        # Create tasks for all requests
        tasks = [make_request() for _ in range(num_requests)]
        await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        # Calculate statistics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[
                18
            ]  # 95th percentile
        else:
            avg_response_time = min_response_time = max_response_time = (
                p95_response_time
            ) = 0

        requests_per_second = successful_requests / total_time if total_time > 0 else 0
        error_rate = failed_requests / num_requests if num_requests > 0 else 0

        result = PerformanceResult(
            endpoint=endpoint,
            total_requests=num_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_time=total_time,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
        )

        self.results.append(result)
        return result

    def print_results(self):
        """Print formatted performance test results."""
        print("\n" + "=" * 80)
        print("PERFORMANCE TEST RESULTS")
        print("=" * 80)

        for result in self.results:
            print(f"\nEndpoint: {result.endpoint}")
            print(f"Total Requests: {result.total_requests}")
            print(f"Successful: {result.successful_requests}")
            print(f"Failed: {result.failed_requests}")
            print(f"Error Rate: {result.error_rate:.2%}")
            print(f"Total Time: {result.total_time:.2f}s")
            print(f"Requests/Second: {result.requests_per_second:.2f}")
            print(f"Response Times:")
            print(f"  Average: {result.avg_response_time*1000:.2f}ms")
            print(f"  Min: {result.min_response_time*1000:.2f}ms")
            print(f"  Max: {result.max_response_time*1000:.2f}ms")
            print(f"  P95: {result.p95_response_time*1000:.2f}ms")

            # Check against targets
            p95_target = 250  # ms
            if result.p95_response_time * 1000 <= p95_target:
                print(
                    f"✅ P95 Response Time: {result.p95_response_time*1000:.2f}ms <= {p95_target}ms"
                )
            else:
                print(
                    f"❌ P95 Response Time: {result.p95_response_time*1000:.2f}ms > {p95_target}ms"
                )

            if result.error_rate <= 0.01:
                print(f"✅ Error Rate: {result.error_rate:.2%} <= 1%")
            else:
                print(f"❌ Error Rate: {result.error_rate:.2%} > 1%")

    def save_results(self, filename: str = "performance_results.json"):
        """Save results to JSON file."""
        results_dict = []
        for result in self.results:
            results_dict.append(
                {
                    "endpoint": result.endpoint,
                    "total_requests": result.total_requests,
                    "successful_requests": result.successful_requests,
                    "failed_requests": result.failed_requests,
                    "total_time": result.total_time,
                    "avg_response_time": result.avg_response_time,
                    "min_response_time": result.min_response_time,
                    "max_response_time": result.max_response_time,
                    "p95_response_time": result.p95_response_time,
                    "requests_per_second": result.requests_per_second,
                    "error_rate": result.error_rate,
                }
            )

        with open(filename, "w") as f:
            json.dump(results_dict, f, indent=2)

        print(f"\nResults saved to {filename}")


async def main():
    """Main performance test function."""
    print("Starting ACCF Research Agent Performance Tests")
    print("=" * 50)

    tester = PerformanceTester()

    # Test endpoints
    endpoints = ["/", "/health", "/detailed", "/ready"]

    for endpoint in endpoints:
        try:
            await tester.test_endpoint(endpoint, num_requests=50, concurrent=5)
        except Exception as e:
            print(f"Failed to test {endpoint}: {e}")

    # Print and save results
    tester.print_results()
    tester.save_results()


if __name__ == "__main__":
    asyncio.run(main())
