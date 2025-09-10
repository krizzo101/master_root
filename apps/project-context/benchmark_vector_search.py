#!/usr/bin/env python3
"""
Vector Search Performance Benchmarks

Comprehensive benchmarking suite for pgvector semantic search performance
in the unified context system.
"""

import asyncio
import json
import logging
import random
import statistics
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import numpy as np
from project_context.core.vector_search import VectorSearchClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# BENCHMARK CONFIGURATION
# ============================================

BENCHMARK_QUERIES = [
    # General programming queries
    "handle database connection errors",
    "implement user authentication",
    "parse JSON response data",
    "validate input parameters",
    "log error messages",
    "cache API responses",
    "process file uploads",
    "encrypt sensitive data",
    "handle async operations",
    "manage memory usage",
    # Python specific
    "Python exception handling",
    "Flask route configuration",
    "Django model relationships",
    "async/await patterns",
    "list comprehensions",
    "decorator implementation",
    "class inheritance",
    "module imports",
    "pytest fixtures",
    "SQLAlchemy queries",
    # JavaScript/Web
    "React component state",
    "Express middleware",
    "Promise error handling",
    "DOM manipulation",
    "API fetch requests",
    "async function syntax",
    "Redux state management",
    "webpack configuration",
    "npm package scripts",
    "CORS configuration",
    # DevOps/Infrastructure
    "Docker container setup",
    "Kubernetes deployment",
    "CI/CD pipeline",
    "nginx configuration",
    "SSL certificate",
    "database migration",
    "load balancing",
    "monitoring setup",
    "backup strategy",
    "security scanning",
]

# ============================================
# BENCHMARK UTILITIES
# ============================================


class BenchmarkResult:
    """Represents a benchmark test result."""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.execution_times: List[float] = []
        self.result_counts: List[int] = []
        self.error_count = 0
        self.start_time = None
        self.end_time = None

    def add_measurement(
        self, execution_time: float, result_count: int = 0, error: bool = False
    ):
        """Add a measurement to the benchmark."""
        if not error:
            self.execution_times.append(execution_time)
            self.result_counts.append(result_count)
        else:
            self.error_count += 1

    def get_statistics(self) -> Dict[str, Any]:
        """Calculate statistics for the benchmark."""
        if not self.execution_times:
            return {
                "test_name": self.test_name,
                "error": "No successful executions",
                "error_count": self.error_count,
            }

        return {
            "test_name": self.test_name,
            "execution_count": len(self.execution_times),
            "error_count": self.error_count,
            "avg_execution_time_ms": statistics.mean(self.execution_times) * 1000,
            "median_execution_time_ms": statistics.median(self.execution_times) * 1000,
            "min_execution_time_ms": min(self.execution_times) * 1000,
            "max_execution_time_ms": max(self.execution_times) * 1000,
            "std_dev_ms": statistics.stdev(self.execution_times) * 1000
            if len(self.execution_times) > 1
            else 0,
            "avg_result_count": statistics.mean(self.result_counts)
            if self.result_counts
            else 0,
            "total_duration_seconds": (self.end_time - self.start_time).total_seconds()
            if self.end_time and self.start_time
            else 0,
            "queries_per_second": len(self.execution_times)
            / (self.end_time - self.start_time).total_seconds()
            if self.end_time and self.start_time
            else 0,
        }


class VectorSearchBenchmark:
    """Comprehensive benchmark suite for vector search operations."""

    def __init__(self, client: VectorSearchClient):
        self.client = client
        self.results: Dict[str, BenchmarkResult] = {}

    async def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all benchmark tests."""
        logger.info("Starting vector search benchmarks...")

        # Check if we have data to benchmark against
        stats = await self.client.get_embedding_stats()
        if stats["overall"]["items_with_embeddings"] < 100:
            logger.warning(
                f"Only {stats['overall']['items_with_embeddings']} items have embeddings. Benchmarks may not be representative."
            )

        # Run individual benchmarks
        await self._benchmark_semantic_search()
        await self._benchmark_code_search()
        await self._benchmark_hybrid_search()
        await self._benchmark_similarity_thresholds()
        await self._benchmark_result_set_sizes()
        await self._benchmark_concurrent_queries()
        await self._benchmark_index_performance()

        # Compile results
        return self._compile_benchmark_report()

    async def _benchmark_semantic_search(self):
        """Benchmark semantic search performance."""
        logger.info("Benchmarking semantic search...")
        benchmark = BenchmarkResult("semantic_search")
        benchmark.start_time = datetime.now()

        for query in BENCHMARK_QUERIES:
            try:
                start_time = time.time()
                results = await self.client.semantic_search(query, max_results=10)
                execution_time = time.time() - start_time

                benchmark.add_measurement(execution_time, len(results))

            except Exception as e:
                logger.error(f"Semantic search failed for '{query}': {e}")
                benchmark.add_measurement(0, 0, error=True)

        benchmark.end_time = datetime.now()
        self.results["semantic_search"] = benchmark

    async def _benchmark_code_search(self):
        """Benchmark code-specific search performance."""
        logger.info("Benchmarking code search...")
        benchmark = BenchmarkResult("code_search")
        benchmark.start_time = datetime.now()

        code_queries = [
            q
            for q in BENCHMARK_QUERIES
            if any(
                term in q.lower()
                for term in [
                    "function",
                    "class",
                    "method",
                    "variable",
                    "python",
                    "javascript",
                ]
            )
        ]

        for query in code_queries:
            try:
                start_time = time.time()
                results = await self.client.code_search(query, max_results=10)
                execution_time = time.time() - start_time

                benchmark.add_measurement(execution_time, len(results))

            except Exception as e:
                logger.error(f"Code search failed for '{query}': {e}")
                benchmark.add_measurement(0, 0, error=True)

        benchmark.end_time = datetime.now()
        self.results["code_search"] = benchmark

    async def _benchmark_hybrid_search(self):
        """Benchmark hybrid (text + vector) search performance."""
        logger.info("Benchmarking hybrid search...")
        benchmark = BenchmarkResult("hybrid_search")
        benchmark.start_time = datetime.now()

        for query in BENCHMARK_QUERIES[:10]:  # Limit to 10 for performance
            try:
                start_time = time.time()
                results = await self.client.hybrid_search(query, max_results=10)
                execution_time = time.time() - start_time

                benchmark.add_measurement(execution_time, len(results))

            except Exception as e:
                logger.error(f"Hybrid search failed for '{query}': {e}")
                benchmark.add_measurement(0, 0, error=True)

        benchmark.end_time = datetime.now()
        self.results["hybrid_search"] = benchmark

    async def _benchmark_similarity_thresholds(self):
        """Benchmark different similarity thresholds."""
        logger.info("Benchmarking similarity thresholds...")

        thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
        query = "handle database connection errors"

        for threshold in thresholds:
            benchmark = BenchmarkResult(f"threshold_{threshold}")
            benchmark.start_time = datetime.now()

            for _ in range(5):  # Run 5 times for each threshold
                try:
                    start_time = time.time()
                    results = await self.client.semantic_search(
                        query, similarity_threshold=threshold, max_results=20
                    )
                    execution_time = time.time() - start_time

                    benchmark.add_measurement(execution_time, len(results))

                except Exception as e:
                    logger.error(f"Threshold {threshold} search failed: {e}")
                    benchmark.add_measurement(0, 0, error=True)

            benchmark.end_time = datetime.now()
            self.results[f"threshold_{threshold}"] = benchmark

    async def _benchmark_result_set_sizes(self):
        """Benchmark different result set sizes."""
        logger.info("Benchmarking result set sizes...")

        sizes = [5, 10, 25, 50, 100]
        query = "implement user authentication"

        for size in sizes:
            benchmark = BenchmarkResult(f"results_{size}")
            benchmark.start_time = datetime.now()

            for _ in range(5):  # Run 5 times for each size
                try:
                    start_time = time.time()
                    results = await self.client.semantic_search(query, max_results=size)
                    execution_time = time.time() - start_time

                    benchmark.add_measurement(execution_time, len(results))

                except Exception as e:
                    logger.error(f"Result size {size} search failed: {e}")
                    benchmark.add_measurement(0, 0, error=True)

            benchmark.end_time = datetime.now()
            self.results[f"results_{size}"] = benchmark

    async def _benchmark_concurrent_queries(self):
        """Benchmark concurrent query performance."""
        logger.info("Benchmarking concurrent queries...")

        concurrency_levels = [1, 2, 5, 10]

        for level in concurrency_levels:
            benchmark = BenchmarkResult(f"concurrent_{level}")
            benchmark.start_time = datetime.now()

            # Run multiple rounds
            for round_num in range(3):
                try:
                    # Prepare queries
                    queries = random.sample(BENCHMARK_QUERIES, level)

                    start_time = time.time()

                    # Execute concurrent searches
                    tasks = [
                        self.client.semantic_search(query, max_results=10)
                        for query in queries
                    ]
                    results_list = await asyncio.gather(*tasks, return_exceptions=True)

                    execution_time = time.time() - start_time

                    # Count successful results
                    successful_results = [
                        r for r in results_list if not isinstance(r, Exception)
                    ]
                    total_results = sum(len(r) for r in successful_results)

                    benchmark.add_measurement(execution_time, total_results)

                except Exception as e:
                    logger.error(f"Concurrent {level} search failed: {e}")
                    benchmark.add_measurement(0, 0, error=True)

            benchmark.end_time = datetime.now()
            self.results[f"concurrent_{level}"] = benchmark

    async def _benchmark_index_performance(self):
        """Benchmark index performance characteristics."""
        logger.info("Benchmarking index performance...")

        # Test different embedding dimensions if available
        queries = ["error handling", "database connection", "user authentication"]

        benchmark = BenchmarkResult("index_performance")
        benchmark.start_time = datetime.now()

        for query in queries:
            try:
                # Test multiple runs to assess index warming
                for run in range(10):
                    start_time = time.time()
                    results = await self.client.semantic_search(query, max_results=50)
                    execution_time = time.time() - start_time

                    benchmark.add_measurement(execution_time, len(results))

            except Exception as e:
                logger.error(f"Index performance test failed for '{query}': {e}")
                benchmark.add_measurement(0, 0, error=True)

        benchmark.end_time = datetime.now()
        self.results["index_performance"] = benchmark

    def _compile_benchmark_report(self) -> Dict[str, Any]:
        """Compile comprehensive benchmark report."""
        report = {
            "benchmark_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(self.results),
                "total_queries": sum(
                    len(b.execution_times) for b in self.results.values()
                ),
                "total_errors": sum(b.error_count for b in self.results.values()),
            },
            "test_results": {},
            "performance_analysis": {},
            "recommendations": [],
        }

        # Individual test results
        for test_name, result in self.results.items():
            report["test_results"][test_name] = result.get_statistics()

        # Performance analysis
        report["performance_analysis"] = self._analyze_performance()

        # Generate recommendations
        report["recommendations"] = self._generate_recommendations()

        return report

    def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance patterns across benchmarks."""
        analysis = {}

        # Compare search types
        search_types = ["semantic_search", "code_search", "hybrid_search"]
        type_performance = {}

        for search_type in search_types:
            if search_type in self.results:
                stats = self.results[search_type].get_statistics()
                type_performance[search_type] = {
                    "avg_time_ms": stats.get("avg_execution_time_ms", 0),
                    "queries_per_second": stats.get("queries_per_second", 0),
                }

        analysis["search_type_comparison"] = type_performance

        # Analyze threshold impact
        threshold_results = {
            k: v for k, v in self.results.items() if k.startswith("threshold_")
        }
        threshold_analysis = {}

        for threshold_name, result in threshold_results.items():
            stats = result.get_statistics()
            threshold_value = threshold_name.split("_")[1]
            threshold_analysis[threshold_value] = {
                "avg_time_ms": stats.get("avg_execution_time_ms", 0),
                "avg_results": stats.get("avg_result_count", 0),
            }

        analysis["threshold_impact"] = threshold_analysis

        # Analyze concurrency scaling
        concurrent_results = {
            k: v for k, v in self.results.items() if k.startswith("concurrent_")
        }
        concurrency_analysis = {}

        for concurrent_name, result in concurrent_results.items():
            stats = result.get_statistics()
            level = concurrent_name.split("_")[1]
            concurrency_analysis[level] = {
                "avg_time_ms": stats.get("avg_execution_time_ms", 0),
                "throughput": stats.get("queries_per_second", 0),
            }

        analysis["concurrency_scaling"] = concurrency_analysis

        return analysis

    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations based on benchmark results."""
        recommendations = []

        # Check semantic search performance
        if "semantic_search" in self.results:
            stats = self.results["semantic_search"].get_statistics()
            avg_time = stats.get("avg_execution_time_ms", 0)

            if avg_time > 1000:
                recommendations.append(
                    "Semantic search queries are taking >1s on average. "
                    "Consider optimizing HNSW index parameters or adding more memory."
                )
            elif avg_time > 500:
                recommendations.append(
                    "Semantic search performance is moderate. "
                    "Monitor query patterns and consider index tuning."
                )

        # Check error rates
        total_queries = sum(
            len(b.execution_times) + b.error_count for b in self.results.values()
        )
        total_errors = sum(b.error_count for b in self.results.values())
        error_rate = (total_errors / total_queries) * 100 if total_queries > 0 else 0

        if error_rate > 5:
            recommendations.append(
                f"High error rate detected ({error_rate:.1f}%). "
                "Check embedding service connectivity and database configuration."
            )

        # Check concurrency scaling
        concurrent_results = {
            k: v for k, v in self.results.items() if k.startswith("concurrent_")
        }
        if len(concurrent_results) >= 2:
            single_perf = None
            multi_perf = None

            if "concurrent_1" in concurrent_results:
                single_perf = (
                    concurrent_results["concurrent_1"]
                    .get_statistics()
                    .get("queries_per_second", 0)
                )
            if "concurrent_10" in concurrent_results:
                multi_perf = (
                    concurrent_results["concurrent_10"]
                    .get_statistics()
                    .get("queries_per_second", 0)
                )

            if single_perf and multi_perf and multi_perf < single_perf * 5:
                recommendations.append(
                    "Concurrency scaling is limited. "
                    "Consider increasing database connection pool size or optimizing indexes."
                )

        return recommendations


# ============================================
# BENCHMARK EXECUTION
# ============================================


async def run_benchmarks() -> Dict[str, Any]:
    """Run comprehensive vector search benchmarks."""
    try:
        async with VectorSearchClient() as client:
            # Verify system is ready
            stats = await client.get_embedding_stats()
            logger.info(
                f"System status: {stats['overall']['items_with_embeddings']} items with embeddings"
            )

            # Run benchmarks
            benchmark_suite = VectorSearchBenchmark(client)
            results = await benchmark_suite.run_all_benchmarks()

            return results

    except Exception as e:
        logger.error(f"Benchmark execution failed: {e}")
        raise


def save_benchmark_results(results: Dict[str, Any], filename: str = None):
    """Save benchmark results to file."""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vector_search_benchmark_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Benchmark results saved to {filename}")


def print_benchmark_summary(results: Dict[str, Any]):
    """Print a summary of benchmark results."""
    print("\n" + "=" * 60)
    print("VECTOR SEARCH PERFORMANCE BENCHMARK RESULTS")
    print("=" * 60)

    summary = results.get("benchmark_summary", {})
    print(f"Timestamp: {summary.get('timestamp', 'Unknown')}")
    print(f"Total Tests: {summary.get('total_tests', 0)}")
    print(f"Total Queries: {summary.get('total_queries', 0)}")
    print(f"Total Errors: {summary.get('total_errors', 0)}")
    print()

    # Performance highlights
    print("PERFORMANCE HIGHLIGHTS:")
    print("-" * 30)

    test_results = results.get("test_results", {})
    for test_name, stats in test_results.items():
        if not test_name.startswith(("threshold_", "results_", "concurrent_")):
            avg_time = stats.get("avg_execution_time_ms", 0)
            qps = stats.get("queries_per_second", 0)
            print(f"{test_name:20s}: {avg_time:6.1f}ms avg, {qps:5.1f} qps")

    # Recommendations
    recommendations = results.get("recommendations", [])
    if recommendations:
        print("\nRECOMMENDATIONS:")
        print("-" * 30)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")

    print("\nFor detailed results, check the saved JSON file.")
    print("=" * 60)


# ============================================
# MAIN EXECUTION
# ============================================


async def main():
    """Main benchmark execution function."""
    logger.info("Starting vector search performance benchmarks...")

    try:
        # Run benchmarks
        results = await run_benchmarks()

        # Save results
        save_benchmark_results(results)

        # Print summary
        print_benchmark_summary(results)

    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
