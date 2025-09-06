"""
Performance benchmarks for Enhanced EnformionClient
Tests performance characteristics, caching efficiency, and scalability
"""

import json
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.providers.enhanced_enformion_client import (
    CacheEntry,
    CircuitBreaker,
    CircuitBreakerConfig,
    EnformionClient,
    MockEnformionClient,
    RateLimiter,
)


class PerformanceBenchmark:
    """Performance benchmark suite for EnformionClient"""

    def __init__(self, use_mock_client: bool = True):
        self.use_mock_client = use_mock_client
        self.results = {}

    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all performance benchmarks"""
        print("🚀 Starting Enhanced EnformionClient Performance Benchmarks")
        print("=" * 60)

        # Basic performance tests
        self.benchmark_single_requests()
        self.benchmark_concurrent_requests()
        self.benchmark_bulk_operations()

        # Caching performance
        self.benchmark_cache_performance()
        self.benchmark_cache_hit_rates()

        # Rate limiting performance
        self.benchmark_rate_limiter()

        # Circuit breaker performance
        self.benchmark_circuit_breaker()

        # Memory usage tests
        self.benchmark_memory_usage()

        # Scalability tests
        self.benchmark_high_volume_operations()

        return self.results

    def benchmark_single_requests(self):
        """Benchmark single request performance"""
        print("\n📊 Benchmarking Single Request Performance...")

        client = MockEnformionClient() if self.use_mock_client else EnformionClient()
        test_cases = [
            ("phone_search", lambda: client.reverse_phone_search("9103925349")),
            (
                "address_search",
                lambda: client.address_search(
                    "123 Main St", city="Charlotte", state="NC"
                ),
            ),
            ("email_search", lambda: client.email_search("test@example.com")),
        ]

        results = {}
        for test_name, test_func in test_cases:
            times = []
            for _ in range(100):  # 100 iterations
                start = time.time()
                try:
                    test_func()
                    end = time.time()
                    times.append((end - start) * 1000)  # Convert to milliseconds
                except Exception as e:
                    print(f"Error in {test_name}: {e}")
                    continue

            if times:
                results[test_name] = {
                    "mean_ms": statistics.mean(times),
                    "median_ms": statistics.median(times),
                    "std_dev_ms": statistics.stdev(times) if len(times) > 1 else 0,
                    "min_ms": min(times),
                    "max_ms": max(times),
                    "p95_ms": self._percentile(times, 95),
                    "p99_ms": self._percentile(times, 99),
                }

                print(f"  {test_name}:")
                print(f"    Mean: {results[test_name]['mean_ms']:.2f}ms")
                print(f"    Median: {results[test_name]['median_ms']:.2f}ms")
                print(f"    P95: {results[test_name]['p95_ms']:.2f}ms")
                print(f"    P99: {results[test_name]['p99_ms']:.2f}ms")

        self.results["single_requests"] = results

    def benchmark_concurrent_requests(self):
        """Benchmark concurrent request performance"""
        print("\n🔄 Benchmarking Concurrent Request Performance...")

        client = MockEnformionClient() if self.use_mock_client else EnformionClient()

        def make_phone_request(phone_num):
            start = time.time()
            try:
                client.reverse_phone_search(f"910392{phone_num:04d}")
                return time.time() - start
            except Exception as e:
                return None

        thread_counts = [1, 5, 10, 20, 50]
        results = {}

        for thread_count in thread_counts:
            print(f"  Testing with {thread_count} threads...")

            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                start_time = time.time()

                # Submit 100 requests
                futures = [executor.submit(make_phone_request, i) for i in range(100)]

                # Collect results
                completion_times = []
                for future in as_completed(futures):
                    result = future.result()
                    if result is not None:
                        completion_times.append(result * 1000)  # Convert to ms

                total_time = time.time() - start_time

                if completion_times:
                    results[f"{thread_count}_threads"] = {
                        "total_time_s": total_time,
                        "requests_per_second": len(completion_times) / total_time,
                        "mean_response_ms": statistics.mean(completion_times),
                        "median_response_ms": statistics.median(completion_times),
                        "p95_response_ms": self._percentile(completion_times, 95),
                        "successful_requests": len(completion_times),
                    }

                    print(
                        f"    RPS: {results[f'{thread_count}_threads']['requests_per_second']:.2f}"
                    )
                    print(
                        f"    Mean Response: {results[f'{thread_count}_threads']['mean_response_ms']:.2f}ms"
                    )
                    print(
                        f"    P95 Response: {results[f'{thread_count}_threads']['p95_response_ms']:.2f}ms"
                    )

        self.results["concurrent_requests"] = results

    def benchmark_bulk_operations(self):
        """Benchmark bulk operation performance"""
        print("\n📦 Benchmarking Bulk Operations...")

        client = MockEnformionClient() if self.use_mock_client else EnformionClient()

        bulk_sizes = [10, 50, 100, 500, 1000]
        results = {}

        for size in bulk_sizes:
            print(f"  Testing bulk size: {size}")

            # Create bulk requests
            requests = []
            for i in range(size):
                if i % 3 == 0:
                    requests.append({"phone": f"910392{i:04d}"})
                elif i % 3 == 1:
                    requests.append({"email": f"test{i}@example.com"})
                else:
                    requests.append({"address": f"{i} Main St", "city": "Charlotte"})

            times = []
            for _ in range(5):  # 5 iterations for each bulk size
                start = time.time()
                try:
                    result = client.bulk_search(requests, search_type="mixed")
                    end = time.time()
                    times.append(end - start)
                except Exception as e:
                    print(f"    Error: {e}")
                    continue

            if times:
                results[f"bulk_{size}"] = {
                    "mean_time_s": statistics.mean(times),
                    "median_time_s": statistics.median(times),
                    "requests_per_second": size / statistics.mean(times),
                    "min_time_s": min(times),
                    "max_time_s": max(times),
                }

                print(f"    Mean Time: {results[f'bulk_{size}']['mean_time_s']:.3f}s")
                print(
                    f"    Effective RPS: {results[f'bulk_{size}']['requests_per_second']:.2f}"
                )

        self.results["bulk_operations"] = results

    def benchmark_cache_performance(self):
        """Benchmark caching performance impact"""
        print("\n💾 Benchmarking Cache Performance...")

        # Test with caching enabled
        client_cached = MockEnformionClient(enable_caching=True)

        # Test with caching disabled
        client_no_cache = MockEnformionClient(enable_caching=False)

        test_requests = [
            ("9103925349", "phone"),
            ("123 Main St", "address"),
            ("test@example.com", "email"),
        ] * 10  # Repeat to test cache hits

        # Benchmark with cache
        print("  Testing with cache enabled...")
        cache_times = []
        cache_start = time.time()

        for request, req_type in test_requests:
            start = time.time()
            if req_type == "phone":
                client_cached.reverse_phone_search(request)
            elif req_type == "address":
                client_cached.address_search(request)
            else:
                client_cached.email_search(request)
            cache_times.append((time.time() - start) * 1000)

        cache_total_time = time.time() - cache_start

        # Benchmark without cache
        print("  Testing with cache disabled...")
        no_cache_times = []
        no_cache_start = time.time()

        for request, req_type in test_requests:
            start = time.time()
            if req_type == "phone":
                client_no_cache.reverse_phone_search(request)
            elif req_type == "address":
                client_no_cache.address_search(request)
            else:
                client_no_cache.email_search(request)
            no_cache_times.append((time.time() - start) * 1000)

        no_cache_total_time = time.time() - no_cache_start

        cache_results = {
            "with_cache": {
                "total_time_s": cache_total_time,
                "mean_request_ms": statistics.mean(cache_times),
                "requests_per_second": len(test_requests) / cache_total_time,
            },
            "without_cache": {
                "total_time_s": no_cache_total_time,
                "mean_request_ms": statistics.mean(no_cache_times),
                "requests_per_second": len(test_requests) / no_cache_total_time,
            },
        }

        # Calculate performance improvement
        cache_results["performance_improvement"] = {
            "time_reduction_percent": (
                (no_cache_total_time - cache_total_time) / no_cache_total_time
            )
            * 100,
            "rps_improvement_percent": (
                (
                    cache_results["with_cache"]["requests_per_second"]
                    - cache_results["without_cache"]["requests_per_second"]
                )
                / cache_results["without_cache"]["requests_per_second"]
            )
            * 100,
        }

        print(
            f"  With Cache - RPS: {cache_results['with_cache']['requests_per_second']:.2f}"
        )
        print(
            f"  Without Cache - RPS: {cache_results['without_cache']['requests_per_second']:.2f}"
        )
        print(
            f"  Performance Improvement: {cache_results['performance_improvement']['rps_improvement_percent']:.1f}%"
        )

        self.results["cache_performance"] = cache_results

    def benchmark_cache_hit_rates(self):
        """Benchmark cache hit rates under different scenarios"""
        print("\n🎯 Benchmarking Cache Hit Rates...")

        # Test cache hit rates with different request patterns
        patterns = {
            "sequential_repeats": self._generate_sequential_repeats,
            "random_repeats": self._generate_random_repeats,
            "working_set": self._generate_working_set,
        }

        results = {}

        for pattern_name, pattern_generator in patterns.items():
            print(f"  Testing pattern: {pattern_name}")

            client = MockEnformionClient(enable_caching=True)
            requests = pattern_generator(100)  # Generate 100 requests

            cache_hits = 0
            total_requests = 0

            start_time = time.time()
            for request in requests:
                # Simulate cache checking (in real implementation)
                if total_requests > 0 and request in requests[:total_requests]:
                    cache_hits += 1

                # Make the request
                if request.startswith("phone:"):
                    phone = request.split(":")[1]
                    client.reverse_phone_search(phone)
                elif request.startswith("email:"):
                    email = request.split(":")[1]
                    client.email_search(email)
                else:  # address
                    address = request.split(":")[1]
                    client.address_search(address)

                total_requests += 1

            total_time = time.time() - start_time
            hit_rate = (cache_hits / total_requests) * 100 if total_requests > 0 else 0

            results[pattern_name] = {
                "total_requests": total_requests,
                "cache_hits": cache_hits,
                "hit_rate_percent": hit_rate,
                "total_time_s": total_time,
                "requests_per_second": total_requests / total_time,
            }

            print(f"    Hit Rate: {hit_rate:.1f}%")
            print(f"    RPS: {total_requests / total_time:.2f}")

        self.results["cache_hit_rates"] = results

    def benchmark_rate_limiter(self):
        """Benchmark rate limiter performance"""
        print("\n⏱️  Benchmarking Rate Limiter...")

        rates = [60, 120, 300, 600]  # requests per minute
        results = {}

        for rate in rates:
            print(f"  Testing rate: {rate} requests/minute")

            limiter = RateLimiter(rate_per_minute=rate)

            # Test burst capacity
            burst_start = time.time()
            burst_acquisitions = 0
            for _ in range(rate):
                if limiter.acquire():
                    burst_acquisitions += 1
                else:
                    break
            burst_time = time.time() - burst_start

            # Test sustained rate
            sustained_start = time.time()
            sustained_acquisitions = 0
            test_duration = 5  # 5 seconds

            while time.time() - sustained_start < test_duration:
                if limiter.acquire():
                    sustained_acquisitions += 1
                else:
                    time.sleep(0.01)  # Small sleep to avoid busy waiting

            actual_duration = time.time() - sustained_start
            sustained_rate = (
                sustained_acquisitions / actual_duration
            ) * 60  # Convert to per minute

            results[f"rate_{rate}"] = {
                "configured_rate": rate,
                "burst_acquisitions": burst_acquisitions,
                "burst_time_s": burst_time,
                "sustained_rate_per_minute": sustained_rate,
                "rate_accuracy_percent": (sustained_rate / rate) * 100,
            }

            print(f"    Burst Capacity: {burst_acquisitions}/{rate}")
            print(
                f"    Sustained Rate: {sustained_rate:.1f}/min (accuracy: {(sustained_rate/rate)*100:.1f}%)"
            )

        self.results["rate_limiter"] = results

    def benchmark_circuit_breaker(self):
        """Benchmark circuit breaker performance"""
        print("\n🔧 Benchmarking Circuit Breaker...")

        configs = [
            CircuitBreakerConfig(
                failure_threshold=3, success_threshold=2, timeout_seconds=1
            ),
            CircuitBreakerConfig(
                failure_threshold=5, success_threshold=3, timeout_seconds=2
            ),
            CircuitBreakerConfig(
                failure_threshold=10, success_threshold=5, timeout_seconds=5
            ),
        ]

        results = {}

        for i, config in enumerate(configs):
            config_name = f"config_{i+1}"
            print(
                f"  Testing {config_name}: failures={config.failure_threshold}, timeout={config.timeout_seconds}s"
            )

            breaker = CircuitBreaker(config)

            # Test failure detection
            def failing_function():
                raise Exception("Test failure")

            def success_function():
                return "success"

            failure_start = time.time()
            failures_until_open = 0

            # Count failures until circuit opens
            try:
                while failures_until_open < 20:  # Max attempts to prevent infinite loop
                    try:
                        breaker.call(failing_function)
                    except Exception:
                        failures_until_open += 1
                        if breaker.state.value == "open":
                            break
            except Exception:
                pass

            failure_time = time.time() - failure_start

            # Test recovery time
            recovery_start = time.time()
            time.sleep(config.timeout_seconds + 0.1)  # Wait for timeout

            # Attempt recovery
            recovery_attempts = 0
            recovered = False

            try:
                for _ in range(10):
                    result = breaker.call(success_function)
                    recovery_attempts += 1
                    if breaker.state.value == "closed":
                        recovered = True
                        break
            except Exception:
                pass

            recovery_time = time.time() - recovery_start

            results[config_name] = {
                "failure_threshold": config.failure_threshold,
                "timeout_seconds": config.timeout_seconds,
                "failures_until_open": failures_until_open,
                "failure_detection_time_s": failure_time,
                "recovery_attempts": recovery_attempts,
                "recovery_time_s": recovery_time,
                "recovered_successfully": recovered,
            }

            print(f"    Failures to open: {failures_until_open}")
            print(
                f"    Recovery: {'✓' if recovered else '✗'} ({recovery_attempts} attempts)"
            )

        self.results["circuit_breaker"] = results

    def benchmark_memory_usage(self):
        """Benchmark memory usage patterns"""
        print("\n💾 Benchmarking Memory Usage...")

        import os

        import psutil

        process = psutil.Process(os.getpid())

        # Baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        client = MockEnformionClient(enable_caching=True, enable_metrics=True)

        # Generate load and measure memory
        memory_measurements = []
        request_counts = [100, 500, 1000, 5000, 10000]

        for count in request_counts:
            print(f"  Testing with {count} requests...")

            # Make requests
            for i in range(count):
                if i % 3 == 0:
                    client.reverse_phone_search(f"910392{i:04d}")
                elif i % 3 == 1:
                    client.email_search(f"test{i}@example.com")
                else:
                    client.address_search(f"{i} Main St")

            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_usage = current_memory - baseline_memory

            memory_measurements.append(
                {
                    "request_count": count,
                    "memory_mb": memory_usage,
                    "memory_per_request_kb": (memory_usage * 1024) / count,
                }
            )

            print(
                f"    Memory Usage: {memory_usage:.2f} MB ({(memory_usage*1024)/count:.2f} KB/request)"
            )

        self.results["memory_usage"] = {
            "baseline_mb": baseline_memory,
            "measurements": memory_measurements,
            "memory_growth_linear": self._analyze_memory_growth(memory_measurements),
        }

    def benchmark_high_volume_operations(self):
        """Benchmark high volume operation performance"""
        print("\n🚀 Benchmarking High Volume Operations...")

        client = MockEnformionClient()

        # Test scenarios
        scenarios = [
            {"name": "sustained_load", "duration_s": 10, "target_rps": 100},
            {"name": "burst_load", "duration_s": 5, "target_rps": 500},
            {"name": "stress_test", "duration_s": 3, "target_rps": 1000},
        ]

        results = {}

        for scenario in scenarios:
            print(
                f"  Testing {scenario['name']}: {scenario['target_rps']} RPS for {scenario['duration_s']}s"
            )

            start_time = time.time()
            end_time = start_time + scenario["duration_s"]
            request_times = []
            successful_requests = 0
            failed_requests = 0

            # Generate load
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = []

                while time.time() < end_time:
                    # Submit requests to maintain target RPS
                    requests_to_submit = min(
                        10, int(scenario["target_rps"] * 0.1)
                    )  # Batch submissions

                    for _ in range(requests_to_submit):
                        future = executor.submit(self._make_test_request, client)
                        futures.append((future, time.time()))

                    time.sleep(0.1)  # 100ms batches

                # Collect results
                for future, submit_time in futures:
                    try:
                        request_start = time.time()
                        result = future.result(timeout=5)
                        request_end = time.time()

                        request_times.append(request_end - request_start)
                        successful_requests += 1
                    except Exception:
                        failed_requests += 1

            actual_duration = time.time() - start_time
            actual_rps = successful_requests / actual_duration

            if request_times:
                results[scenario["name"]] = {
                    "target_rps": scenario["target_rps"],
                    "actual_rps": actual_rps,
                    "successful_requests": successful_requests,
                    "failed_requests": failed_requests,
                    "success_rate_percent": (
                        successful_requests / (successful_requests + failed_requests)
                    )
                    * 100,
                    "mean_response_time_ms": statistics.mean(request_times) * 1000,
                    "p95_response_time_ms": self._percentile(request_times, 95) * 1000,
                    "p99_response_time_ms": self._percentile(request_times, 99) * 1000,
                }

                print(f"    Actual RPS: {actual_rps:.2f}")
                print(
                    f"    Success Rate: {results[scenario['name']]['success_rate_percent']:.1f}%"
                )
                print(
                    f"    P95 Response: {results[scenario['name']]['p95_response_time_ms']:.2f}ms"
                )

        self.results["high_volume"] = results

    # Helper methods

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def _generate_sequential_repeats(self, count: int) -> List[str]:
        """Generate sequential repeat pattern for cache testing"""
        requests = []
        base_requests = [
            "phone:9103925349",
            "email:test@example.com",
            "address:123 Main St",
        ]

        for i in range(count):
            requests.append(base_requests[i % len(base_requests)])

        return requests

    def _generate_random_repeats(self, count: int) -> List[str]:
        """Generate random repeat pattern for cache testing"""
        import random

        requests = []
        base_requests = [f"phone:910392{i:04d}" for i in range(20)]

        for _ in range(count):
            requests.append(random.choice(base_requests))

        return requests

    def _generate_working_set(self, count: int) -> List[str]:
        """Generate working set pattern for cache testing"""
        requests = []
        working_set = [f"phone:910392{i:04d}" for i in range(10)]

        for i in range(count):
            if i < 50:  # First 50% populate working set
                requests.append(working_set[i % len(working_set)])
            else:  # Second 50% mostly use working set
                if i % 10 == 0:  # 10% new requests
                    requests.append(f"phone:910392{1000+i:04d}")
                else:  # 90% from working set
                    requests.append(working_set[i % len(working_set)])

        return requests

    def _analyze_memory_growth(self, measurements: List[Dict]) -> bool:
        """Analyze if memory growth is linear"""
        if len(measurements) < 3:
            return True

        # Check if memory per request is relatively constant
        mem_per_req = [m["memory_per_request_kb"] for m in measurements]
        variance = statistics.variance(mem_per_req) if len(mem_per_req) > 1 else 0
        mean = statistics.mean(mem_per_req)

        # Consider linear if coefficient of variation < 0.5
        cv = (variance**0.5) / mean if mean > 0 else 0
        return cv < 0.5

    def _make_test_request(self, client):
        """Make a test request for load testing"""
        import random

        request_type = random.choice(["phone", "email", "address"])

        if request_type == "phone":
            return client.reverse_phone_search(f"910392{random.randint(1000, 9999)}")
        elif request_type == "email":
            return client.email_search(f"test{random.randint(1, 1000)}@example.com")
        else:
            return client.address_search(f"{random.randint(1, 999)} Main St")

    def print_summary(self):
        """Print benchmark summary"""
        print("\n" + "=" * 60)
        print("📋 PERFORMANCE BENCHMARK SUMMARY")
        print("=" * 60)

        if "single_requests" in self.results:
            print("\n🔍 Single Request Performance:")
            for endpoint, metrics in self.results["single_requests"].items():
                print(
                    f"  {endpoint}: {metrics['mean_ms']:.2f}ms avg, {metrics['p95_ms']:.2f}ms P95"
                )

        if "concurrent_requests" in self.results:
            print("\n🔄 Concurrent Performance (Best):")
            best_rps = max(
                [
                    m["requests_per_second"]
                    for m in self.results["concurrent_requests"].values()
                ]
            )
            print(f"  Max RPS: {best_rps:.2f}")

        if "cache_performance" in self.results:
            improvement = self.results["cache_performance"]["performance_improvement"][
                "rps_improvement_percent"
            ]
            print(f"\n💾 Cache Performance Improvement: {improvement:.1f}%")

        if "memory_usage" in self.results:
            measurements = self.results["memory_usage"]["measurements"]
            max_memory = max([m["memory_mb"] for m in measurements])
            print(f"\n💾 Max Memory Usage: {max_memory:.2f} MB")

        if "high_volume" in self.results:
            print("\n🚀 High Volume Results:")
            for scenario, metrics in self.results["high_volume"].items():
                print(
                    f"  {scenario}: {metrics['actual_rps']:.2f} RPS, {metrics['success_rate_percent']:.1f}% success"
                )

        print("\n✅ Benchmark Complete!")


def main():
    """Run performance benchmarks"""
    benchmark = PerformanceBenchmark(use_mock_client=True)

    print("Enhanced EnformionClient Performance Benchmark Suite")
    print("Note: Using MockEnformionClient for consistent, reproducible results")
    print("For real API testing, set use_mock_client=False")

    # Run all benchmarks
    results = benchmark.run_all_benchmarks()

    # Print summary
    benchmark.print_summary()

    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"benchmark_results_{timestamp}.json"

    with open(results_file, "w") as f:
        # Convert datetime objects to strings for JSON serialization
        json.dump(results, f, indent=2, default=str)

    print(f"\n📊 Detailed results saved to: {results_file}")

    return results


if __name__ == "__main__":
    main()
