#!/usr/bin/env python3
"""
Escalation System Performance Benchmarks and Metrics Collection

This script provides comprehensive performance testing and benchmarking for the
escalation system, measuring throughput, latency, resource usage, and scalability
characteristics under various load conditions.
"""

import asyncio
import json
import logging
import statistics
import sys
import time
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from escalation_integration import (
    EscalationAwareOrchestrator,
    EscalationConfig,
    create_development_orchestrator,
)
from escalation_manager import (
    EscalationReason,
    EscalationRequest,
    EscalationType,
    IntelligentAgent,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Single benchmark test result"""

    test_name: str
    start_time: float
    end_time: float
    duration: float
    success_count: int
    failure_count: int
    total_operations: int
    throughput: float  # operations per second
    average_latency: float  # seconds
    min_latency: float
    max_latency: float
    p95_latency: float
    p99_latency: float
    memory_usage_mb: float
    cpu_usage_percent: float
    errors: List[str] = field(default_factory=list)
    additional_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "test_name": self.test_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "total_operations": self.total_operations,
            "success_rate": self.success_count / self.total_operations
            if self.total_operations > 0
            else 0,
            "throughput": self.throughput,
            "average_latency": self.average_latency,
            "min_latency": self.min_latency,
            "max_latency": self.max_latency,
            "p95_latency": self.p95_latency,
            "p99_latency": self.p99_latency,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "errors": self.errors,
            "additional_metrics": self.additional_metrics,
        }


class EscalationBenchmarker:
    """
    Comprehensive performance benchmarking system for escalation capabilities.

    Provides:
    1. Throughput benchmarks - escalations per second under load
    2. Latency benchmarks - response time distributions
    3. Scalability benchmarks - performance vs concurrent escalations
    4. Resource usage benchmarks - memory and CPU utilization
    5. Stress testing - system behavior at limits
    6. Long-running stability benchmarks
    """

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.benchmark_dir = output_dir / "escalation_benchmarks"
        self.benchmark_dir.mkdir(parents=True, exist_ok=True)

        # Benchmark results storage
        self.benchmark_results: Dict[str, BenchmarkResult] = {}
        self.performance_baselines: Dict[str, float] = {
            "min_throughput": 10.0,  # escalations per second
            "max_avg_latency": 2.0,  # seconds
            "max_p95_latency": 5.0,  # seconds
            "max_memory_mb": 500,  # MB
            "max_cpu_percent": 80.0,  # %
        }

        # Test configurations
        self.benchmark_configurations = {
            "throughput_light": {"concurrent": 5, "total": 100, "duration": 30},
            "throughput_medium": {"concurrent": 15, "total": 300, "duration": 60},
            "throughput_heavy": {"concurrent": 25, "total": 500, "duration": 90},
            "latency_single": {"concurrent": 1, "total": 50, "duration": 60},
            "latency_concurrent": {"concurrent": 10, "total": 200, "duration": 120},
            "scalability_ramp": {
                "start": 1,
                "end": 30,
                "step": 3,
                "operations_per_level": 20,
            },
            "stress_burst": {"concurrent": 50, "total": 1000, "duration": 180},
            "stability_long": {"concurrent": 5, "total": 1000, "duration": 300},
        }

        logger.info(
            f"EscalationBenchmarker initialized with {len(self.benchmark_configurations)} test configs"
        )

    async def run_comprehensive_benchmarks(self) -> Dict[str, Any]:
        """Run complete benchmark suite and generate performance report"""
        logger.info("Starting comprehensive escalation system benchmarks")

        start_time = time.time()

        try:
            # Initialize orchestrator for benchmarking
            orchestrator = create_development_orchestrator(
                output_dir=self.benchmark_dir,
                tokens=["benchmark_token"],
                max_parallel=10,
                enable_escalation=True,
            )

            # Run benchmark categories
            await self._run_throughput_benchmarks(orchestrator)
            await self._run_latency_benchmarks(orchestrator)
            await self._run_scalability_benchmarks(orchestrator)
            await self._run_resource_usage_benchmarks(orchestrator)
            await self._run_stress_tests(orchestrator)
            await self._run_stability_benchmarks(orchestrator)

            # Cleanup
            await orchestrator.shutdown()

            total_time = time.time() - start_time

            # Generate performance report
            report = await self._generate_benchmark_report(total_time)

            logger.info(f"Benchmarks completed in {total_time:.2f}s")
            return report

        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            logger.error(traceback.format_exc())

            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "partial_results": {
                    name: result.to_dict()
                    for name, result in self.benchmark_results.items()
                },
            }

    async def _run_throughput_benchmarks(
        self, orchestrator: EscalationAwareOrchestrator
    ):
        """Measure throughput under different load levels"""
        logger.info("Running throughput benchmarks")

        throughput_tests = ["throughput_light", "throughput_medium", "throughput_heavy"]

        for test_name in throughput_tests:
            config = self.benchmark_configurations[test_name]
            logger.info(f"Starting throughput test: {test_name}")

            start_time = time.time()
            latencies = []
            successes = 0
            failures = 0

            # Start resource monitoring
            initial_memory = self._get_memory_usage()
            initial_cpu = self._get_cpu_usage()

            # Create semaphore for concurrency control
            semaphore = asyncio.Semaphore(config["concurrent"])

            async def send_escalation(escalation_id: str) -> Tuple[bool, float]:
                async with semaphore:
                    op_start = time.time()
                    try:
                        request = EscalationRequest(
                            escalation_id=escalation_id,
                            agent_id=f"throughput_agent_{escalation_id}",
                            agent_uuid=str(uuid.uuid4()),
                            escalation_type=EscalationType.REPLACEMENT,
                            escalation_reason=EscalationReason.FAILURE_THRESHOLD,
                            problem_description=f"Throughput test escalation {escalation_id}",
                            priority="normal",
                        )

                        result = (
                            await orchestrator.escalation_manager.handle_escalation(
                                request
                            )
                        )
                        op_duration = time.time() - op_start
                        return (result is not None, op_duration)

                    except Exception as e:
                        op_duration = time.time() - op_start
                        logger.warning(f"Escalation {escalation_id} failed: {e}")
                        return (False, op_duration)

            # Execute throughput test
            tasks = []
            for i in range(config["total"]):
                escalation_id = f"{test_name}_{i}_{uuid.uuid4().hex[:8]}"
                tasks.append(send_escalation(escalation_id))

                # Add small delay to spread the load
                if i % config["concurrent"] == 0 and i > 0:
                    await asyncio.sleep(0.1)

            # Wait for completion or timeout
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=config["duration"],
                )
            except asyncio.TimeoutError:
                logger.warning(f"Throughput test {test_name} timed out")
                results = []

            # Process results
            for result in results:
                if isinstance(result, tuple):
                    success, latency = result
                    latencies.append(latency)
                    if success:
                        successes += 1
                    else:
                        failures += 1
                else:
                    failures += 1
                    latencies.append(config["duration"])  # Assume timeout latency

            end_time = time.time()
            duration = end_time - start_time

            # Calculate metrics
            final_memory = self._get_memory_usage()
            final_cpu = self._get_cpu_usage()

            if latencies:
                avg_latency = statistics.mean(latencies)
                min_latency = min(latencies)
                max_latency = max(latencies)
                p95_latency = (
                    statistics.quantiles(latencies, n=20)[18]
                    if len(latencies) > 5
                    else max_latency
                )
                p99_latency = (
                    statistics.quantiles(latencies, n=100)[98]
                    if len(latencies) > 10
                    else max_latency
                )
            else:
                avg_latency = min_latency = max_latency = p95_latency = p99_latency = 0

            total_ops = successes + failures
            throughput = total_ops / duration if duration > 0 else 0

            # Store benchmark result
            self.benchmark_results[test_name] = BenchmarkResult(
                test_name=test_name,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                success_count=successes,
                failure_count=failures,
                total_operations=total_ops,
                throughput=throughput,
                average_latency=avg_latency,
                min_latency=min_latency,
                max_latency=max_latency,
                p95_latency=p95_latency,
                p99_latency=p99_latency,
                memory_usage_mb=final_memory - initial_memory,
                cpu_usage_percent=final_cpu,
                additional_metrics={
                    "concurrent_limit": config["concurrent"],
                    "target_operations": config["total"],
                    "timeout_seconds": config["duration"],
                },
            )

            logger.info(
                f"Throughput test {test_name} completed: {throughput:.1f} ops/sec, {successes}/{total_ops} success"
            )

    async def _run_latency_benchmarks(self, orchestrator: EscalationAwareOrchestrator):
        """Measure latency characteristics"""
        logger.info("Running latency benchmarks")

        latency_tests = ["latency_single", "latency_concurrent"]

        for test_name in latency_tests:
            config = self.benchmark_configurations[test_name]
            logger.info(f"Starting latency test: {test_name}")

            start_time = time.time()
            latencies = []
            successes = 0
            failures = 0

            # Start resource monitoring
            initial_memory = self._get_memory_usage()

            # Create semaphore for concurrency control
            semaphore = asyncio.Semaphore(config["concurrent"])

            async def measure_escalation_latency(
                escalation_id: str,
            ) -> Tuple[bool, float]:
                async with semaphore:
                    op_start = time.time()
                    try:
                        request = EscalationRequest(
                            escalation_id=escalation_id,
                            agent_id=f"latency_agent_{escalation_id}",
                            agent_uuid=str(uuid.uuid4()),
                            escalation_type=EscalationType.REPLACEMENT,
                            escalation_reason=EscalationReason.MISSING_PERMISSIONS,
                            problem_description=f"Latency measurement escalation {escalation_id}",
                            priority="high",  # High priority for latency tests
                        )

                        result = (
                            await orchestrator.escalation_manager.handle_escalation(
                                request
                            )
                        )

                        # Wait for response to measure complete cycle
                        await asyncio.sleep(0.5)  # Allow processing time
                        response = (
                            await orchestrator.escalation_manager.comm_bus.get_response(
                                escalation_id
                            )
                        )

                        op_duration = time.time() - op_start
                        return (
                            result is not None and response is not None,
                            op_duration,
                        )

                    except Exception as e:
                        op_duration = time.time() - op_start
                        logger.debug(f"Latency test {escalation_id} failed: {e}")
                        return (False, op_duration)

            # Execute latency measurements
            batch_size = max(1, config["total"] // 20)  # Process in batches

            for batch_start in range(0, config["total"], batch_size):
                batch_end = min(batch_start + batch_size, config["total"])
                batch_tasks = []

                for i in range(batch_start, batch_end):
                    escalation_id = f"{test_name}_{i}_{uuid.uuid4().hex[:8]}"
                    batch_tasks.append(measure_escalation_latency(escalation_id))

                try:
                    batch_results = await asyncio.wait_for(
                        asyncio.gather(*batch_tasks, return_exceptions=True),
                        timeout=config["duration"] / 10,  # Per-batch timeout
                    )

                    for result in batch_results:
                        if isinstance(result, tuple):
                            success, latency = result
                            latencies.append(latency)
                            if success:
                                successes += 1
                            else:
                                failures += 1
                        else:
                            failures += 1
                            latencies.append(10.0)  # Assume failure latency

                except asyncio.TimeoutError:
                    logger.warning(f"Latency test {test_name} batch timed out")
                    failures += len(batch_tasks)

                # Brief pause between batches
                await asyncio.sleep(0.1)

            end_time = time.time()
            duration = end_time - start_time

            # Calculate detailed latency statistics
            final_memory = self._get_memory_usage()

            if latencies:
                avg_latency = statistics.mean(latencies)
                min_latency = min(latencies)
                max_latency = max(latencies)

                # Calculate percentiles
                sorted_latencies = sorted(latencies)
                p95_index = int(len(sorted_latencies) * 0.95)
                p99_index = int(len(sorted_latencies) * 0.99)
                p95_latency = (
                    sorted_latencies[p95_index]
                    if p95_index < len(sorted_latencies)
                    else max_latency
                )
                p99_latency = (
                    sorted_latencies[p99_index]
                    if p99_index < len(sorted_latencies)
                    else max_latency
                )

                # Additional latency metrics
                median_latency = statistics.median(latencies)
                latency_stddev = (
                    statistics.stdev(latencies) if len(latencies) > 1 else 0
                )
            else:
                avg_latency = min_latency = max_latency = p95_latency = p99_latency = 0
                median_latency = latency_stddev = 0

            total_ops = successes + failures
            throughput = total_ops / duration if duration > 0 else 0

            # Store detailed latency results
            self.benchmark_results[test_name] = BenchmarkResult(
                test_name=test_name,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                success_count=successes,
                failure_count=failures,
                total_operations=total_ops,
                throughput=throughput,
                average_latency=avg_latency,
                min_latency=min_latency,
                max_latency=max_latency,
                p95_latency=p95_latency,
                p99_latency=p99_latency,
                memory_usage_mb=final_memory - initial_memory,
                cpu_usage_percent=self._get_cpu_usage(),
                additional_metrics={
                    "median_latency": median_latency,
                    "latency_stddev": latency_stddev,
                    "concurrent_requests": config["concurrent"],
                    "total_measurements": len(latencies),
                },
            )

            logger.info(
                f"Latency test {test_name} completed: avg={avg_latency:.3f}s, p95={p95_latency:.3f}s, p99={p99_latency:.3f}s"
            )

    async def _run_scalability_benchmarks(
        self, orchestrator: EscalationAwareOrchestrator
    ):
        """Test scalability characteristics"""
        logger.info("Running scalability benchmarks")

        config = self.benchmark_configurations["scalability_ramp"]

        scalability_results = []

        for concurrency in range(config["start"], config["end"] + 1, config["step"]):
            logger.info(f"Testing scalability at concurrency level: {concurrency}")

            level_start = time.time()
            latencies = []
            successes = 0
            failures = 0

            # Monitor resources at this concurrency level
            initial_memory = self._get_memory_usage()
            initial_cpu = self._get_cpu_usage()

            semaphore = asyncio.Semaphore(concurrency)

            async def concurrent_escalation(escalation_id: str) -> Tuple[bool, float]:
                async with semaphore:
                    op_start = time.time()
                    try:
                        request = EscalationRequest(
                            escalation_id=escalation_id,
                            agent_id=f"scale_agent_{escalation_id}",
                            agent_uuid=str(uuid.uuid4()),
                            escalation_type=EscalationType.SUB_SWARM,
                            escalation_reason=EscalationReason.COMPLEX_DEBUGGING,
                            problem_description=f"Scalability test escalation {escalation_id}",
                            specialist_types_needed=["troubleshoot", "solution"],
                            time_budget=60,
                        )

                        result = (
                            await orchestrator.escalation_manager.handle_escalation(
                                request
                            )
                        )
                        op_duration = time.time() - op_start
                        return (result is not None, op_duration)

                    except Exception as e:
                        op_duration = time.time() - op_start
                        return (False, op_duration)

            # Execute operations at this concurrency level
            tasks = []
            for i in range(config["operations_per_level"]):
                escalation_id = f"scale_{concurrency}_{i}_{uuid.uuid4().hex[:8]}"
                tasks.append(concurrent_escalation(escalation_id))

            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=60,  # 1 minute timeout per level
                )

                for result in results:
                    if isinstance(result, tuple):
                        success, latency = result
                        latencies.append(latency)
                        if success:
                            successes += 1
                        else:
                            failures += 1
                    else:
                        failures += 1
                        latencies.append(60.0)

            except asyncio.TimeoutError:
                logger.warning(
                    f"Scalability test at concurrency {concurrency} timed out"
                )
                failures += len(tasks)

            level_duration = time.time() - level_start
            final_memory = self._get_memory_usage()
            final_cpu = self._get_cpu_usage()

            # Calculate metrics for this concurrency level
            total_ops = successes + failures
            throughput = total_ops / level_duration if level_duration > 0 else 0
            avg_latency = statistics.mean(latencies) if latencies else 0
            p95_latency = (
                statistics.quantiles(latencies, n=20)[18]
                if len(latencies) > 5
                else avg_latency
            )

            scalability_results.append(
                {
                    "concurrency_level": concurrency,
                    "throughput": throughput,
                    "average_latency": avg_latency,
                    "p95_latency": p95_latency,
                    "success_rate": successes / total_ops if total_ops > 0 else 0,
                    "memory_delta_mb": final_memory - initial_memory,
                    "cpu_usage_percent": final_cpu,
                    "duration": level_duration,
                }
            )

            logger.info(
                f"Scalability level {concurrency}: {throughput:.1f} ops/sec, {avg_latency:.3f}s avg latency"
            )

            # Brief pause between levels
            await asyncio.sleep(2)

        # Store scalability benchmark results
        total_duration = sum(result["duration"] for result in scalability_results)
        max_throughput = (
            max(result["throughput"] for result in scalability_results)
            if scalability_results
            else 0
        )

        self.benchmark_results["scalability_ramp"] = BenchmarkResult(
            test_name="scalability_ramp",
            start_time=time.time() - total_duration,
            end_time=time.time(),
            duration=total_duration,
            success_count=sum(
                int(r["success_rate"] * config["operations_per_level"])
                for r in scalability_results
            ),
            failure_count=sum(
                config["operations_per_level"]
                - int(r["success_rate"] * config["operations_per_level"])
                for r in scalability_results
            ),
            total_operations=len(scalability_results) * config["operations_per_level"],
            throughput=max_throughput,
            average_latency=statistics.mean(
                [r["average_latency"] for r in scalability_results]
            ),
            min_latency=min([r["average_latency"] for r in scalability_results])
            if scalability_results
            else 0,
            max_latency=max([r["average_latency"] for r in scalability_results])
            if scalability_results
            else 0,
            p95_latency=max([r["p95_latency"] for r in scalability_results])
            if scalability_results
            else 0,
            p99_latency=max([r["p95_latency"] for r in scalability_results])
            if scalability_results
            else 0,
            memory_usage_mb=max([r["memory_delta_mb"] for r in scalability_results])
            if scalability_results
            else 0,
            cpu_usage_percent=max([r["cpu_usage_percent"] for r in scalability_results])
            if scalability_results
            else 0,
            additional_metrics={
                "scalability_curve": scalability_results,
                "max_tested_concurrency": config["end"],
                "operations_per_level": config["operations_per_level"],
            },
        )

    async def _run_resource_usage_benchmarks(
        self, orchestrator: EscalationAwareOrchestrator
    ):
        """Monitor resource usage patterns"""
        logger.info("Running resource usage benchmarks")

        # Monitor resource usage during moderate load
        config = self.benchmark_configurations["throughput_medium"]

        start_time = time.time()
        resource_snapshots = []

        # Start background resource monitoring
        monitoring_task = asyncio.create_task(
            self._monitor_resources(
                resource_snapshots, interval=1.0, duration=config["duration"]
            )
        )

        # Run escalations while monitoring resources
        semaphore = asyncio.Semaphore(config["concurrent"])
        successes = 0
        failures = 0

        async def resource_test_escalation(escalation_id: str) -> bool:
            async with semaphore:
                try:
                    request = EscalationRequest(
                        escalation_id=escalation_id,
                        agent_id=f"resource_agent_{escalation_id}",
                        agent_uuid=str(uuid.uuid4()),
                        escalation_type=EscalationType.REPLACEMENT,
                        escalation_reason=EscalationReason.CONTEXT_EXHAUSTION,
                        problem_description=f"Resource monitoring test escalation {escalation_id}",
                        required_context=["large_context_data"]
                        * 10,  # Simulate memory usage
                        priority="normal",
                    )

                    result = await orchestrator.escalation_manager.handle_escalation(
                        request
                    )
                    return result is not None

                except Exception:
                    return False

        # Execute resource usage test
        tasks = []
        for i in range(config["total"]):
            escalation_id = f"resource_test_{i}_{uuid.uuid4().hex[:8]}"
            tasks.append(resource_test_escalation(escalation_id))

            # Spread load over time
            if i % 10 == 0:
                await asyncio.sleep(0.5)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, bool) and result:
                successes += 1
            else:
                failures += 1

        # Stop resource monitoring
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            pass

        end_time = time.time()
        duration = end_time - start_time

        # Analyze resource usage patterns
        if resource_snapshots:
            memory_values = [s["memory_mb"] for s in resource_snapshots]
            cpu_values = [s["cpu_percent"] for s in resource_snapshots]

            peak_memory = max(memory_values)
            avg_memory = statistics.mean(memory_values)
            peak_cpu = max(cpu_values)
            avg_cpu = statistics.mean(cpu_values)
        else:
            peak_memory = avg_memory = peak_cpu = avg_cpu = 0

        total_ops = successes + failures
        throughput = total_ops / duration if duration > 0 else 0

        self.benchmark_results["resource_usage"] = BenchmarkResult(
            test_name="resource_usage",
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            success_count=successes,
            failure_count=failures,
            total_operations=total_ops,
            throughput=throughput,
            average_latency=duration / total_ops if total_ops > 0 else 0,
            min_latency=0,
            max_latency=duration,
            p95_latency=duration * 0.95,
            p99_latency=duration * 0.99,
            memory_usage_mb=peak_memory,
            cpu_usage_percent=peak_cpu,
            additional_metrics={
                "resource_snapshots": resource_snapshots,
                "peak_memory_mb": peak_memory,
                "average_memory_mb": avg_memory,
                "peak_cpu_percent": peak_cpu,
                "average_cpu_percent": avg_cpu,
                "memory_growth": peak_memory - memory_values[0] if memory_values else 0,
            },
        )

        logger.info(
            f"Resource usage test: peak memory {peak_memory:.1f}MB, peak CPU {peak_cpu:.1f}%"
        )

    async def _run_stress_tests(self, orchestrator: EscalationAwareOrchestrator):
        """Run stress tests to find system limits"""
        logger.info("Running stress tests")

        config = self.benchmark_configurations["stress_burst"]

        start_time = time.time()
        latencies = []
        successes = 0
        failures = 0

        # Monitor system health during stress
        initial_memory = self._get_memory_usage()

        # Create high concurrency scenario
        semaphore = asyncio.Semaphore(config["concurrent"])

        async def stress_escalation(escalation_id: str) -> Tuple[bool, float]:
            async with semaphore:
                op_start = time.time()
                try:
                    # Mix different escalation types for stress
                    escalation_types = [
                        EscalationType.REPLACEMENT,
                        EscalationType.SUB_SWARM,
                    ]
                    escalation_type = escalation_types[
                        hash(escalation_id) % len(escalation_types)
                    ]

                    request = EscalationRequest(
                        escalation_id=escalation_id,
                        agent_id=f"stress_agent_{escalation_id}",
                        agent_uuid=str(uuid.uuid4()),
                        escalation_type=escalation_type,
                        escalation_reason=EscalationReason.FAILURE_THRESHOLD,
                        problem_description=f"Stress test escalation {escalation_id} with complex requirements",
                        attempted_solutions=[
                            "solution_" + str(i) for i in range(5)
                        ],  # Add complexity
                        required_tools=["tool_" + str(i) for i in range(3)],
                        specialist_types_needed=["spec_" + str(i) for i in range(4)]
                        if escalation_type == EscalationType.SUB_SWARM
                        else [],
                        priority="normal",
                    )

                    result = await orchestrator.escalation_manager.handle_escalation(
                        request
                    )
                    op_duration = time.time() - op_start
                    return (result is not None, op_duration)

                except Exception as e:
                    op_duration = time.time() - op_start
                    logger.debug(f"Stress test escalation {escalation_id} failed: {e}")
                    return (False, op_duration)

        # Execute stress test in bursts
        burst_size = config["concurrent"] * 2
        total_completed = 0

        for burst_start in range(0, config["total"], burst_size):
            burst_end = min(burst_start + burst_size, config["total"])
            burst_tasks = []

            for i in range(burst_start, burst_end):
                escalation_id = f"stress_{i}_{uuid.uuid4().hex[:8]}"
                burst_tasks.append(stress_escalation(escalation_id))

            try:
                burst_results = await asyncio.wait_for(
                    asyncio.gather(*burst_tasks, return_exceptions=True),
                    timeout=30,  # 30 second timeout per burst
                )

                for result in burst_results:
                    if isinstance(result, tuple):
                        success, latency = result
                        latencies.append(latency)
                        if success:
                            successes += 1
                        else:
                            failures += 1
                    else:
                        failures += 1
                        latencies.append(30.0)  # Timeout latency

                total_completed += len(burst_tasks)

            except asyncio.TimeoutError:
                logger.warning(f"Stress test burst {burst_start}-{burst_end} timed out")
                failures += len(burst_tasks)
                total_completed += len(burst_tasks)

            # Check if system is still responsive
            try:
                dashboard = await asyncio.wait_for(
                    orchestrator.get_escalation_dashboard(), timeout=5
                )
                if dashboard is None:
                    logger.error("Dashboard not responsive during stress test")
                    break
            except asyncio.TimeoutError:
                logger.error(
                    "Dashboard timeout during stress test - system may be overloaded"
                )
                break

            # Brief pause between bursts
            await asyncio.sleep(1)

        end_time = time.time()
        duration = end_time - start_time

        # Calculate stress test metrics
        final_memory = self._get_memory_usage()
        final_cpu = self._get_cpu_usage()

        if latencies:
            avg_latency = statistics.mean(latencies)
            p95_latency = (
                statistics.quantiles(latencies, n=20)[18]
                if len(latencies) > 5
                else avg_latency
            )
            p99_latency = (
                statistics.quantiles(latencies, n=100)[98]
                if len(latencies) > 10
                else avg_latency
            )
        else:
            avg_latency = p95_latency = p99_latency = 0

        total_ops = successes + failures
        throughput = total_ops / duration if duration > 0 else 0

        self.benchmark_results["stress_burst"] = BenchmarkResult(
            test_name="stress_burst",
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            success_count=successes,
            failure_count=failures,
            total_operations=total_ops,
            throughput=throughput,
            average_latency=avg_latency,
            min_latency=min(latencies) if latencies else 0,
            max_latency=max(latencies) if latencies else 0,
            p95_latency=p95_latency,
            p99_latency=p99_latency,
            memory_usage_mb=final_memory - initial_memory,
            cpu_usage_percent=final_cpu,
            additional_metrics={
                "concurrent_limit": config["concurrent"],
                "target_operations": config["total"],
                "completed_operations": total_completed,
                "system_remained_responsive": total_completed == config["total"],
            },
        )

        logger.info(
            f"Stress test completed: {throughput:.1f} ops/sec, {successes}/{total_ops} success, system responsive: {total_completed == config['total']}"
        )

    async def _run_stability_benchmarks(
        self, orchestrator: EscalationAwareOrchestrator
    ):
        """Test long-running stability"""
        logger.info("Running stability benchmarks")

        config = self.benchmark_configurations["stability_long"]

        start_time = time.time()
        stability_snapshots = []
        successes = 0
        failures = 0

        # Track system health over time
        monitoring_task = asyncio.create_task(
            self._monitor_stability(
                orchestrator,
                stability_snapshots,
                interval=30.0,
                duration=config["duration"],
            )
        )

        # Run steady load over extended period
        semaphore = asyncio.Semaphore(config["concurrent"])

        async def stability_escalation(escalation_id: str) -> bool:
            async with semaphore:
                try:
                    request = EscalationRequest(
                        escalation_id=escalation_id,
                        agent_id=f"stability_agent_{escalation_id}",
                        agent_uuid=str(uuid.uuid4()),
                        escalation_type=EscalationType.REPLACEMENT,
                        escalation_reason=EscalationReason.MISSING_DEPENDENCIES,
                        problem_description=f"Long-term stability test escalation {escalation_id}",
                        priority="normal",
                    )

                    result = await orchestrator.escalation_manager.handle_escalation(
                        request
                    )
                    return result is not None

                except Exception:
                    return False

        # Execute operations over time with steady rate
        operations_per_minute = config["total"] // (config["duration"] // 60)
        completed_operations = 0

        start_test_time = time.time()

        while (
            time.time() - start_test_time < config["duration"]
            and completed_operations < config["total"]
        ):
            # Send batch of operations
            batch_size = min(
                operations_per_minute // 6, config["total"] - completed_operations
            )  # Every 10 seconds
            batch_tasks = []

            for i in range(batch_size):
                escalation_id = (
                    f"stability_{completed_operations + i}_{uuid.uuid4().hex[:8]}"
                )
                batch_tasks.append(stability_escalation(escalation_id))

            if batch_tasks:
                try:
                    batch_results = await asyncio.wait_for(
                        asyncio.gather(*batch_tasks, return_exceptions=True),
                        timeout=60,  # 1 minute timeout per batch
                    )

                    for result in batch_results:
                        if isinstance(result, bool) and result:
                            successes += 1
                        else:
                            failures += 1

                    completed_operations += len(batch_tasks)

                except asyncio.TimeoutError:
                    logger.warning("Stability test batch timed out")
                    failures += len(batch_tasks)
                    completed_operations += len(batch_tasks)

            # Wait for next batch
            await asyncio.sleep(10)

        # Stop stability monitoring
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            pass

        end_time = time.time()
        duration = end_time - start_time

        # Analyze stability metrics
        if stability_snapshots:
            dashboard_response_times = [
                s.get("dashboard_response_time", 0) for s in stability_snapshots
            ]
            memory_values = [s.get("memory_mb", 0) for s in stability_snapshots]

            avg_response_time = statistics.mean(dashboard_response_times)
            memory_growth = (
                max(memory_values) - min(memory_values) if memory_values else 0
            )
            system_health_checks_passed = sum(
                1 for s in stability_snapshots if s.get("system_healthy", False)
            )
        else:
            avg_response_time = memory_growth = 0
            system_health_checks_passed = 0

        total_ops = successes + failures
        throughput = total_ops / duration if duration > 0 else 0

        self.benchmark_results["stability_long"] = BenchmarkResult(
            test_name="stability_long",
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            success_count=successes,
            failure_count=failures,
            total_operations=total_ops,
            throughput=throughput,
            average_latency=avg_response_time,
            min_latency=min(dashboard_response_times)
            if dashboard_response_times
            else 0,
            max_latency=max(dashboard_response_times)
            if dashboard_response_times
            else 0,
            p95_latency=statistics.quantiles(dashboard_response_times, n=20)[18]
            if len(dashboard_response_times) > 5
            else 0,
            p99_latency=statistics.quantiles(dashboard_response_times, n=100)[98]
            if len(dashboard_response_times) > 10
            else 0,
            memory_usage_mb=memory_growth,
            cpu_usage_percent=self._get_cpu_usage(),
            additional_metrics={
                "stability_snapshots": stability_snapshots,
                "system_health_checks_passed": system_health_checks_passed,
                "total_health_checks": len(stability_snapshots),
                "memory_growth_mb": memory_growth,
                "dashboard_avg_response_time": avg_response_time,
                "completed_operations": completed_operations,
                "target_operations": config["total"],
            },
        )

        logger.info(
            f"Stability test completed: {throughput:.1f} ops/sec over {duration:.1f}s, {system_health_checks_passed}/{len(stability_snapshots)} health checks passed"
        )

    async def _monitor_resources(
        self, snapshots: List[Dict], interval: float, duration: float
    ):
        """Monitor system resources during benchmarks"""
        start_time = time.time()

        while time.time() - start_time < duration:
            snapshot = {
                "timestamp": time.time(),
                "memory_mb": self._get_memory_usage(),
                "cpu_percent": self._get_cpu_usage(),
                "elapsed_time": time.time() - start_time,
            }
            snapshots.append(snapshot)

            await asyncio.sleep(interval)

    async def _monitor_stability(
        self,
        orchestrator: EscalationAwareOrchestrator,
        snapshots: List[Dict],
        interval: float,
        duration: float,
    ):
        """Monitor system stability during long-running tests"""
        start_time = time.time()

        while time.time() - start_time < duration:
            snapshot_start = time.time()

            try:
                # Test dashboard responsiveness
                dashboard = await asyncio.wait_for(
                    orchestrator.get_escalation_dashboard(), timeout=10
                )
                dashboard_response_time = time.time() - snapshot_start
                system_healthy = dashboard is not None

            except asyncio.TimeoutError:
                dashboard_response_time = 10.0
                system_healthy = False
            except Exception:
                dashboard_response_time = 10.0
                system_healthy = False

            snapshot = {
                "timestamp": time.time(),
                "elapsed_time": time.time() - start_time,
                "dashboard_response_time": dashboard_response_time,
                "system_healthy": system_healthy,
                "memory_mb": self._get_memory_usage(),
                "cpu_percent": self._get_cpu_usage(),
            }
            snapshots.append(snapshot)

            await asyncio.sleep(interval)

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        try:
            return psutil.cpu_percent(interval=0.1)
        except:
            return 0.0

    async def _generate_benchmark_report(self, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive benchmark report"""
        logger.info("Generating benchmark report")

        # Evaluate performance against baselines
        performance_assessment = {}

        for test_name, result in self.benchmark_results.items():
            assessment = {}

            # Throughput assessment
            if result.throughput >= self.performance_baselines["min_throughput"]:
                assessment["throughput"] = "PASS"
            else:
                assessment["throughput"] = "FAIL"

            # Latency assessment
            if result.average_latency <= self.performance_baselines["max_avg_latency"]:
                assessment["average_latency"] = "PASS"
            else:
                assessment["average_latency"] = "FAIL"

            if result.p95_latency <= self.performance_baselines["max_p95_latency"]:
                assessment["p95_latency"] = "PASS"
            else:
                assessment["p95_latency"] = "FAIL"

            # Resource usage assessment
            if result.memory_usage_mb <= self.performance_baselines["max_memory_mb"]:
                assessment["memory_usage"] = "PASS"
            else:
                assessment["memory_usage"] = "FAIL"

            if (
                result.cpu_usage_percent
                <= self.performance_baselines["max_cpu_percent"]
            ):
                assessment["cpu_usage"] = "PASS"
            else:
                assessment["cpu_usage"] = "FAIL"

            # Overall assessment
            passed_checks = sum(1 for v in assessment.values() if v == "PASS")
            assessment["overall"] = (
                "PASS" if passed_checks >= len(assessment) * 0.8 else "FAIL"
            )

            performance_assessment[test_name] = assessment

        # Calculate benchmark summary
        all_results = list(self.benchmark_results.values())
        summary = {
            "total_benchmarks": len(all_results),
            "passed_benchmarks": sum(
                1 for r in performance_assessment.values() if r["overall"] == "PASS"
            ),
            "max_throughput": max(r.throughput for r in all_results)
            if all_results
            else 0,
            "min_latency": min(r.average_latency for r in all_results)
            if all_results
            else 0,
            "max_memory_usage": max(r.memory_usage_mb for r in all_results)
            if all_results
            else 0,
            "total_operations": sum(r.total_operations for r in all_results),
            "total_successful_operations": sum(r.success_count for r in all_results),
            "overall_success_rate": sum(r.success_count for r in all_results)
            / sum(r.total_operations for r in all_results)
            if sum(r.total_operations for r in all_results) > 0
            else 0,
        }

        report = {
            "benchmark_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_execution_time": total_time,
                "benchmarks_completed": len(self.benchmark_results),
                "benchmark_version": "1.0.0",
            },
            "performance_summary": summary,
            "performance_baselines": self.performance_baselines,
            "performance_assessment": performance_assessment,
            "detailed_results": {
                name: result.to_dict()
                for name, result in self.benchmark_results.items()
            },
            "recommendations": self._generate_performance_recommendations(
                performance_assessment
            ),
            "system_limits": {
                "max_tested_concurrency": 50,
                "max_sustained_throughput": summary["max_throughput"],
                "stable_latency_under_load": min(
                    r.p95_latency for r in all_results if "latency" in r.test_name
                )
                if all_results
                else 0,
                "memory_efficiency": summary["max_memory_usage"]
                / summary["total_operations"]
                if summary["total_operations"] > 0
                else 0,
            },
        }

        # Save benchmark report
        report_file = self.benchmark_dir / "escalation_benchmark_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        # Save CSV summary for analysis
        csv_file = self.benchmark_dir / "benchmark_results.csv"
        self._save_csv_results(csv_file)

        logger.info(f"Benchmark report saved to: {report_file}")
        logger.info(
            f"Performance assessment: {summary['passed_benchmarks']}/{summary['total_benchmarks']} benchmarks passed"
        )

        return report

    def _generate_performance_recommendations(self, assessments: Dict) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []

        failed_tests = {
            name: assessment
            for name, assessment in assessments.items()
            if assessment["overall"] == "FAIL"
        }

        if failed_tests:
            recommendations.append(
                "Performance optimization needed for failed benchmark tests"
            )

        # Specific recommendations based on failures
        throughput_failures = [
            name
            for name, assessment in assessments.items()
            if assessment.get("throughput") == "FAIL"
        ]
        if throughput_failures:
            recommendations.append(
                "Optimize throughput - consider connection pooling, async optimizations, or horizontal scaling"
            )

        latency_failures = [
            name
            for name, assessment in assessments.items()
            if assessment.get("average_latency") == "FAIL"
            or assessment.get("p95_latency") == "FAIL"
        ]
        if latency_failures:
            recommendations.append(
                "Reduce latency - optimize critical path operations and reduce I/O blocking"
            )

        memory_failures = [
            name
            for name, assessment in assessments.items()
            if assessment.get("memory_usage") == "FAIL"
        ]
        if memory_failures:
            recommendations.append(
                "Optimize memory usage - implement object pooling, reduce memory allocations, check for leaks"
            )

        cpu_failures = [
            name
            for name, assessment in assessments.items()
            if assessment.get("cpu_usage") == "FAIL"
        ]
        if cpu_failures:
            recommendations.append(
                "Reduce CPU usage - optimize algorithms, reduce computational complexity"
            )

        return recommendations

    def _save_csv_results(self, csv_file: Path):
        """Save benchmark results in CSV format for analysis"""
        try:
            import csv

            with open(csv_file, "w", newline="") as f:
                writer = csv.writer(f)

                # Header
                writer.writerow(
                    [
                        "Test Name",
                        "Duration (s)",
                        "Total Operations",
                        "Success Count",
                        "Success Rate",
                        "Throughput (ops/s)",
                        "Avg Latency (s)",
                        "P95 Latency (s)",
                        "P99 Latency (s)",
                        "Memory Usage (MB)",
                        "CPU Usage (%)",
                    ]
                )

                # Data rows
                for result in self.benchmark_results.values():
                    writer.writerow(
                        [
                            result.test_name,
                            round(result.duration, 2),
                            result.total_operations,
                            result.success_count,
                            round(
                                result.success_count / result.total_operations
                                if result.total_operations > 0
                                else 0,
                                3,
                            ),
                            round(result.throughput, 2),
                            round(result.average_latency, 3),
                            round(result.p95_latency, 3),
                            round(result.p99_latency, 3),
                            round(result.memory_usage_mb, 1),
                            round(result.cpu_usage_percent, 1),
                        ]
                    )

            logger.info(f"CSV results saved to: {csv_file}")

        except Exception as e:
            logger.warning(f"Failed to save CSV results: {e}")


async def main():
    """Main benchmark runner"""
    print("⚡ Starting Comprehensive Escalation System Benchmarks")

    # Setup
    output_dir = Path("./escalation_benchmark_output")
    output_dir.mkdir(exist_ok=True)

    # Initialize benchmarker
    benchmarker = EscalationBenchmarker(output_dir)

    try:
        # Run benchmarks
        report = await benchmarker.run_comprehensive_benchmarks()

        # Display results
        print("\n" + "=" * 80)
        print("📊 ESCALATION SYSTEM BENCHMARK RESULTS")
        print("=" * 80)

        summary = report.get("performance_summary", {})
        print(
            f"🏆 Benchmarks Passed: {summary.get('passed_benchmarks', 0)}/{summary.get('total_benchmarks', 0)}"
        )
        print(
            f"🚀 Max Throughput: {summary.get('max_throughput', 0):.1f} operations/second"
        )
        print(f"⚡ Min Latency: {summary.get('min_latency', 0):.3f} seconds")
        print(f"💾 Max Memory: {summary.get('max_memory_usage', 0):.1f} MB")
        print(f"✅ Overall Success Rate: {summary.get('overall_success_rate', 0):.1%}")

        # Show individual benchmark results
        print("\n📋 INDIVIDUAL BENCHMARK RESULTS:")
        assessment = report.get("performance_assessment", {})
        for test_name, result in assessment.items():
            status = "✅ PASS" if result["overall"] == "PASS" else "❌ FAIL"
            test_display = test_name.replace("_", " ").title()
            print(f"  {status} {test_display}")

        # Show system limits
        limits = report.get("system_limits", {})
        print(f"\n🔧 SYSTEM CHARACTERISTICS:")
        print(f"  Max Tested Concurrency: {limits.get('max_tested_concurrency', 0)}")
        print(
            f"  Max Sustained Throughput: {limits.get('max_sustained_throughput', 0):.1f} ops/sec"
        )
        print(
            f"  Stable P95 Latency: {limits.get('stable_latency_under_load', 0):.3f}s"
        )
        print(
            f"  Memory Efficiency: {limits.get('memory_efficiency', 0):.2f} MB/operation"
        )

        if report.get("recommendations"):
            print("\n💡 PERFORMANCE RECOMMENDATIONS:")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"  {i}. {rec}")

        print(
            f"\n📄 Full benchmark report: {output_dir}/escalation_benchmark_output/escalation_benchmark_report.json"
        )
        print(
            f"📈 CSV results: {output_dir}/escalation_benchmark_output/benchmark_results.csv"
        )
        print("=" * 80)

        # Exit with appropriate code
        passed_benchmarks = summary.get("passed_benchmarks", 0)
        total_benchmarks = summary.get("total_benchmarks", 1)

        if passed_benchmarks >= total_benchmarks * 0.8:  # 80% pass rate
            print("🎉 Escalation system performance is acceptable!")
            return 0
        else:
            print("⚠️  Escalation system needs performance optimization")
            return 1

    except Exception as e:
        print(f"❌ Benchmarking failed: {e}")
        return 2


if __name__ == "__main__":
    # Require psutil for resource monitoring
    try:
        import psutil
    except ImportError:
        print(
            "Error: psutil required for benchmarking. Install with: pip install psutil"
        )
        exit(3)

    exit_code = asyncio.run(main())
    exit(exit_code)
