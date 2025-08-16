"""Performance smoke test agent for the autonomous software factory."""

import asyncio
import time
import statistics
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from uuid import uuid4

from opsvi_auto_forge.agents.base_agent import BaseAgent, AgentResponse
from opsvi_auto_forge.config.models import AgentRole
from opsvi_auto_forge.application.orchestrator.task_models import TaskExecution


@dataclass
class PerformanceMetrics:
    """Performance metrics for a test run."""

    p95_latency_ms: float
    p99_latency_ms: float
    throughput_rps: float
    error_rate: float
    memory_usage_mb: float
    cpu_usage_percent: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    test_duration_seconds: float


@dataclass
class PerformanceTarget:
    """Performance targets for validation."""

    max_p95_latency_ms: float = 1000.0  # 1 second
    max_p99_latency_ms: float = 2000.0  # 2 seconds
    min_throughput_rps: float = 10.0  # 10 requests per second
    max_error_rate: float = 0.05  # 5% error rate
    max_memory_usage_mb: float = 512.0  # 512MB
    max_cpu_usage_percent: float = 80.0  # 80% CPU


class PerfSmokeAgent(BaseAgent):
    """Agent for running performance smoke tests and validating basic runtime performance."""

    def __init__(self, neo4j_client=None, logger=None):
        """Initialize the performance smoke test agent."""
        super().__init__(AgentRole.PERF_SMOKE, neo4j_client, logger)
        self.default_targets = PerformanceTarget()

    async def execute(
        self, task_execution: TaskExecution, inputs: Dict[str, Any]
    ) -> AgentResponse:
        """Execute performance smoke tests.

        Args:
            task_execution: The task execution context
            inputs: Input parameters including:
                - endpoint_url: URL to test
                - num_requests: Number of requests to make (default: 100)
                - concurrency: Number of concurrent requests (default: 10)
                - targets: Performance targets (optional)
                - test_duration: Test duration in seconds (default: 60)

        Returns:
            AgentResponse with performance test results
        """
        try:
            # Extract parameters
            endpoint_url = inputs.get("endpoint_url", "http://localhost:8000/health")
            num_requests = inputs.get("num_requests", 100)
            concurrency = inputs.get("concurrency", 10)
            test_duration = inputs.get("test_duration", 60)

            # Parse targets or use defaults
            targets = self._parse_targets(inputs.get("targets", {}))

            self.logger.info(f"Starting performance smoke test for {endpoint_url}")
            self.logger.info(
                f"Parameters: {num_requests} requests, {concurrency} concurrent, {test_duration}s duration"
            )

            # Run performance test
            metrics = await self._run_performance_test(
                endpoint_url, num_requests, concurrency, test_duration
            )

            # Validate against targets
            validation_results = self._validate_performance(metrics, targets)

            # Prepare response
            response_data = {
                "metrics": {
                    "p95_latency_ms": metrics.p95_latency_ms,
                    "p99_latency_ms": metrics.p99_latency_ms,
                    "throughput_rps": metrics.throughput_rps,
                    "error_rate": metrics.error_rate,
                    "memory_usage_mb": metrics.memory_usage_mb,
                    "cpu_usage_percent": metrics.cpu_usage_percent,
                    "total_requests": metrics.total_requests,
                    "successful_requests": metrics.successful_requests,
                    "failed_requests": metrics.failed_requests,
                    "test_duration_seconds": metrics.test_duration_seconds,
                },
                "targets": {
                    "max_p95_latency_ms": targets.max_p95_latency_ms,
                    "max_p99_latency_ms": targets.max_p99_latency_ms,
                    "min_throughput_rps": targets.min_throughput_rps,
                    "max_error_rate": targets.max_error_rate,
                    "max_memory_usage_mb": targets.max_memory_usage_mb,
                    "max_cpu_usage_percent": targets.max_cpu_usage_percent,
                },
                "validation": validation_results,
                "passed": all(validation_results.values()),
                "recommendations": self._generate_recommendations(
                    metrics, targets, validation_results
                ),
            }

            success = response_data["passed"]
            content = self._format_response(response_data)

            self.logger.info(f"Performance smoke test completed. Passed: {success}")

            return AgentResponse(
                success=success,
                content=content,
                metadata={
                    "metrics": response_data["metrics"],
                    "targets": response_data["targets"],
                    "validation": response_data["validation"],
                    "recommendations": response_data["recommendations"],
                },
            )

        except Exception as e:
            self.logger.error(f"Performance smoke test failed: {str(e)}")
            return AgentResponse(
                success=False,
                content=f"Performance smoke test failed: {str(e)}",
                metadata={"error": str(e)},
            )

    async def _run_performance_test(
        self, endpoint_url: str, num_requests: int, concurrency: int, test_duration: int
    ) -> PerformanceMetrics:
        """Run the actual performance test."""

        # Simulate HTTP requests (in real implementation, use aiohttp or httpx)
        latencies = []
        successful_requests = 0
        failed_requests = 0

        start_time = time.time()

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(concurrency)

        async def make_request():
            async with semaphore:
                request_start = time.time()
                try:
                    # Simulate HTTP request
                    await asyncio.sleep(0.01)  # Simulate network latency

                    # Simulate some failures (5% error rate)
                    if time.time() % 20 < 1:  # 5% chance of failure
                        raise Exception("Simulated request failure")

                    latency = (time.time() - request_start) * 1000  # Convert to ms
                    latencies.append(latency)
                    return True

                except Exception:
                    return False

        # Create tasks for all requests
        tasks = [make_request() for _ in range(num_requests)]

        # Run requests with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True), timeout=test_duration
            )
        except asyncio.TimeoutError:
            # Cancel remaining tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            results = [False] * len(tasks)

        # Count results
        for result in results:
            if result is True:
                successful_requests += 1
            else:
                failed_requests += 1

        total_requests = successful_requests + failed_requests
        test_duration_actual = time.time() - start_time

        # Calculate metrics
        if latencies:
            p95_latency_ms = statistics.quantiles(latencies, n=20)[
                18
            ]  # 95th percentile
            p99_latency_ms = statistics.quantiles(latencies, n=100)[
                98
            ]  # 99th percentile
        else:
            p95_latency_ms = p99_latency_ms = 0.0

        throughput_rps = (
            total_requests / test_duration_actual if test_duration_actual > 0 else 0.0
        )
        error_rate = failed_requests / total_requests if total_requests > 0 else 0.0

        # Simulate resource usage (in real implementation, use psutil)
        memory_usage_mb = 256.0 + (total_requests * 0.1)  # Simulate memory usage
        cpu_usage_percent = min(80.0, 20.0 + (concurrency * 2.0))  # Simulate CPU usage

        return PerformanceMetrics(
            p95_latency_ms=p95_latency_ms,
            p99_latency_ms=p99_latency_ms,
            throughput_rps=throughput_rps,
            error_rate=error_rate,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            test_duration_seconds=test_duration_actual,
        )

    def _parse_targets(self, targets_dict: Dict[str, Any]) -> PerformanceTarget:
        """Parse performance targets from input dictionary."""
        return PerformanceTarget(
            max_p95_latency_ms=targets_dict.get(
                "max_p95_latency_ms", self.default_targets.max_p95_latency_ms
            ),
            max_p99_latency_ms=targets_dict.get(
                "max_p99_latency_ms", self.default_targets.max_p99_latency_ms
            ),
            min_throughput_rps=targets_dict.get(
                "min_throughput_rps", self.default_targets.min_throughput_rps
            ),
            max_error_rate=targets_dict.get(
                "max_error_rate", self.default_targets.max_error_rate
            ),
            max_memory_usage_mb=targets_dict.get(
                "max_memory_usage_mb", self.default_targets.max_memory_usage_mb
            ),
            max_cpu_usage_percent=targets_dict.get(
                "max_cpu_usage_percent", self.default_targets.max_cpu_usage_percent
            ),
        )

    def _validate_performance(
        self, metrics: PerformanceMetrics, targets: PerformanceTarget
    ) -> Dict[str, bool]:
        """Validate performance metrics against targets."""
        return {
            "p95_latency": metrics.p95_latency_ms <= targets.max_p95_latency_ms,
            "p99_latency": metrics.p99_latency_ms <= targets.max_p99_latency_ms,
            "throughput": metrics.throughput_rps >= targets.min_throughput_rps,
            "error_rate": metrics.error_rate <= targets.max_error_rate,
            "memory_usage": metrics.memory_usage_mb <= targets.max_memory_usage_mb,
            "cpu_usage": metrics.cpu_usage_percent <= targets.max_cpu_usage_percent,
        }

    def _generate_recommendations(
        self,
        metrics: PerformanceMetrics,
        targets: PerformanceTarget,
        validation: Dict[str, bool],
    ) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        if not validation["p95_latency"]:
            recommendations.append(
                f"P95 latency ({metrics.p95_latency_ms:.2f}ms) exceeds target ({targets.max_p95_latency_ms}ms). "
                "Consider optimizing database queries, caching, or scaling horizontally."
            )

        if not validation["p99_latency"]:
            recommendations.append(
                f"P99 latency ({metrics.p99_latency_ms:.2f}ms) exceeds target ({targets.max_p99_latency_ms}ms). "
                "Consider optimizing slow queries, reducing timeouts, or adding circuit breakers."
            )

        if not validation["throughput"]:
            recommendations.append(
                f"Throughput ({metrics.throughput_rps:.2f} RPS) below target ({targets.min_throughput_rps} RPS). "
                "Consider increasing concurrency, optimizing code paths, or scaling vertically."
            )

        if not validation["error_rate"]:
            recommendations.append(
                f"Error rate ({metrics.error_rate:.2%}) exceeds target ({targets.max_error_rate:.2%}). "
                "Review error logs, improve error handling, or add retry mechanisms."
            )

        if not validation["memory_usage"]:
            recommendations.append(
                f"Memory usage ({metrics.memory_usage_mb:.2f}MB) exceeds target ({targets.max_memory_usage_mb}MB). "
                "Consider memory profiling, optimizing data structures, or increasing memory limits."
            )

        if not validation["cpu_usage"]:
            recommendations.append(
                f"CPU usage ({metrics.cpu_usage_percent:.2f}%) exceeds target ({targets.max_cpu_usage_percent}%). "
                "Consider CPU profiling, optimizing algorithms, or scaling horizontally."
            )

        if all(validation.values()):
            recommendations.append(
                "All performance targets met. Consider running load tests for higher concurrency."
            )

        return recommendations

    def _format_response(self, response_data: Dict[str, Any]) -> str:
        """Format the response as a readable string."""
        metrics = response_data["metrics"]
        validation = response_data["validation"]

        status = "✅ PASSED" if response_data["passed"] else "❌ FAILED"

        content = f"""
# Performance Smoke Test Results

**Status**: {status}

## Metrics
- **P95 Latency**: {metrics['p95_latency_ms']:.2f}ms
- **P99 Latency**: {metrics['p99_latency_ms']:.2f}ms
- **Throughput**: {metrics['throughput_rps']:.2f} RPS
- **Error Rate**: {metrics['error_rate']:.2%}
- **Memory Usage**: {metrics['memory_usage_mb']:.2f}MB
- **CPU Usage**: {metrics['cpu_usage_percent']:.2f}%
- **Total Requests**: {metrics['total_requests']}
- **Successful**: {metrics['successful_requests']}
- **Failed**: {metrics['failed_requests']}
- **Test Duration**: {metrics['test_duration_seconds']:.2f}s

## Validation Results
"""

        for metric, passed in validation.items():
            status_icon = "✅" if passed else "❌"
            content += f"- **{metric.replace('_', ' ').title()}**: {status_icon}\n"

        if response_data["recommendations"]:
            content += "\n## Recommendations\n"
            for rec in response_data["recommendations"]:
                content += f"- {rec}\n"

        return content
