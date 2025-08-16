"""
Performance benchmarking system for enhanced agent systems.

This module provides comprehensive performance analysis including:
- Execution time profiling and analysis
- Memory usage tracking and optimization
- Throughput measurement and scaling analysis
- Resource utilization monitoring
- Comparative performance analysis
"""

import asyncio
import json
import logging
import psutil
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable
import tracemalloc

from src.agents.integration_test_suite import TestAgent, MockTool
from src.coordination.enhanced_message_bus import EnhancedMessageBus

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""

    name: str
    category: str
    duration: float
    success: bool
    iterations: int
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def throughput(self) -> float:
        """Calculate throughput (operations per second)."""
        return self.iterations / self.duration if self.duration > 0 else 0

    @property
    def avg_time_per_operation(self) -> float:
        """Calculate average time per operation."""
        return self.duration / self.iterations if self.iterations > 0 else 0


class PerformanceBenchmark:
    """Comprehensive performance benchmarking system."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize benchmark system."""
        self.config = config or {}
        self.results: List[BenchmarkResult] = []
        self.baseline_results: Dict[str, BenchmarkResult] = {}
        self.logger = logging.getLogger(f"{__name__}.PerformanceBenchmark")

        # Memory tracking
        self.memory_snapshots: List[Tuple[str, int]] = []

    async def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run comprehensive performance benchmark suite."""
        self.logger.info("Starting comprehensive performance benchmarks")

        # Start memory tracking
        tracemalloc.start()
        start_time = time.time()

        try:
            # Agent performance benchmarks
            await self.benchmark_agent_task_processing()
            await self.benchmark_agent_tool_execution()
            await self.benchmark_agent_message_handling()

            # Message bus benchmarks
            await self.benchmark_message_bus_throughput()
            await self.benchmark_message_bus_routing()
            await self.benchmark_message_bus_reliability()

            # System-level benchmarks
            await self.benchmark_multi_agent_coordination()
            await self.benchmark_resource_utilization()
            await self.benchmark_scalability()

            total_time = time.time() - start_time

            # Generate analysis
            analysis = self._analyze_results(total_time)

            self.logger.info(f"Performance benchmarks completed in {total_time:.2f}s")
            return analysis

        finally:
            # Stop memory tracking
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            self.memory_snapshots.append(("final", peak))

    async def benchmark_agent_task_processing(self) -> None:
        """Benchmark agent task processing performance."""
        self.logger.info("Benchmarking agent task processing")

        agent = TestAgent("benchmark_agent_1")
        await agent.initialize()
        await agent.start()

        try:
            # Benchmark 1: Simple task processing
            await self._run_benchmark(
                "simple_task_processing",
                "agent_performance",
                lambda: agent.process_task({"id": "simple", "type": "simple"}),
                iterations=100,
            )

            # Benchmark 2: Concurrent task processing
            await self._run_concurrent_benchmark(
                "concurrent_task_processing",
                "agent_performance",
                lambda: agent.process_task({"id": "concurrent", "type": "simple"}),
                concurrent_count=20,
                iterations=5,
            )

            # Benchmark 3: Long-running task processing
            await self._run_benchmark(
                "long_running_task_processing",
                "agent_performance",
                lambda: agent.process_task(
                    {"id": "long", "type": "long_running", "duration": 0.5}
                ),
                iterations=10,
            )

        finally:
            await agent.stop()

    async def benchmark_agent_tool_execution(self) -> None:
        """Benchmark agent tool execution performance."""
        self.logger.info("Benchmarking agent tool execution")

        agent = TestAgent("benchmark_agent_2")

        # Add performance test tools
        agent.add_test_tool(MockTool("fast_tool", 0.01, 0.0))
        agent.add_test_tool(MockTool("medium_tool", 0.1, 0.0))
        agent.add_test_tool(MockTool("slow_tool", 0.5, 0.0))

        await agent.initialize()
        await agent.start()

        try:
            # Benchmark tool execution with different speeds
            for tool_name in ["fast_tool", "medium_tool", "slow_tool"]:
                await self._run_benchmark(
                    f"{tool_name}_execution",
                    "tool_performance",
                    lambda tn=tool_name: agent.execute_tool(tn, {"test": "benchmark"}),
                    iterations=50 if tool_name == "fast_tool" else 20,
                )

            # Benchmark tool caching effectiveness
            cache_task = lambda: agent.execute_tool("fast_tool", {"cached": "data"})

            # First run (cache miss)
            miss_result = await self._run_benchmark(
                "tool_cache_miss", "caching_performance", cache_task, iterations=10
            )

            # Second run (cache hit)
            hit_result = await self._run_benchmark(
                "tool_cache_hit", "caching_performance", cache_task, iterations=10
            )

            # Calculate cache efficiency
            if miss_result and hit_result:
                cache_improvement = (
                    miss_result.avg_time_per_operation
                    / hit_result.avg_time_per_operation
                )
                hit_result.metrics["cache_improvement_factor"] = cache_improvement

        finally:
            await agent.stop()

    async def benchmark_agent_message_handling(self) -> None:
        """Benchmark agent message handling performance."""
        self.logger.info("Benchmarking agent message handling")

        # Create message bus and agents
        bus = EnhancedMessageBus()
        await bus.start()

        agent1 = TestAgent("benchmark_sender")
        agent2 = TestAgent("benchmark_receiver")

        await agent1.initialize()
        await agent2.initialize()
        await agent1.start()
        await agent2.start()

        # Register with bus
        await bus.register_agent(agent1.agent_id, agent1._handle_message, ["sender"])
        await bus.register_agent(agent2.agent_id, agent2._handle_message, ["receiver"])

        try:
            from src.agents.base_agent import AgentMessage, MessageType

            # Benchmark message sending
            async def send_message():
                message = AgentMessage(
                    type=MessageType.NOTIFICATION,
                    content={"benchmark": "data"},
                    sender_id=agent1.agent_id,
                    recipient_id=agent2.agent_id,
                )
                return await bus.send_message(message)

            await self._run_benchmark(
                "message_sending", "messaging_performance", send_message, iterations=100
            )

            # Benchmark broadcast messaging
            async def broadcast_message():
                message = AgentMessage(
                    type=MessageType.NOTIFICATION,
                    content={"broadcast": "data"},
                    sender_id=agent1.agent_id,
                )
                return await bus.send_message(
                    message, required_capabilities=["receiver"]
                )

            await self._run_benchmark(
                "broadcast_messaging",
                "messaging_performance",
                broadcast_message,
                iterations=50,
            )

        finally:
            await agent1.stop()
            await agent2.stop()
            await bus.stop()

    async def benchmark_message_bus_throughput(self) -> None:
        """Benchmark message bus throughput capabilities."""
        self.logger.info("Benchmarking message bus throughput")

        bus = EnhancedMessageBus()
        await bus.start()

        # Create multiple agents for throughput testing
        agents = []
        for i in range(5):
            agent = TestAgent(f"throughput_agent_{i}")
            await agent.initialize()
            await agent.start()
            await bus.register_agent(
                agent.agent_id, agent._handle_message, ["throughput_test"]
            )
            agents.append(agent)

        try:
            from src.agents.base_agent import AgentMessage, MessageType

            # High-frequency message sending
            async def send_burst():
                messages = []
                for i in range(50):
                    message = AgentMessage(
                        type=MessageType.NOTIFICATION,
                        content={"burst": i},
                        sender_id=agents[0].agent_id,
                    )
                    messages.append(
                        bus.send_message(
                            message, required_capabilities=["throughput_test"]
                        )
                    )

                return await asyncio.gather(*messages)

            await self._run_benchmark(
                "high_frequency_messaging",
                "throughput_performance",
                send_burst,
                iterations=5,
            )

        finally:
            for agent in agents:
                await agent.stop()
            await bus.stop()

    async def benchmark_message_bus_routing(self) -> None:
        """Benchmark message bus routing strategies."""
        self.logger.info("Benchmarking message bus routing")

        from src.coordination.enhanced_message_bus import RoutingStrategy

        strategies = [
            RoutingStrategy.ROUND_ROBIN,
            RoutingStrategy.LEAST_BUSY,
            RoutingStrategy.RANDOM,
        ]

        for strategy in strategies:
            bus = EnhancedMessageBus(routing_strategy=strategy)
            await bus.start()

            # Create agents with different capabilities
            agents = []
            for i in range(3):
                agent = TestAgent(f"routing_agent_{i}")
                await agent.initialize()
                await agent.start()
                await bus.register_agent(
                    agent.agent_id,
                    agent._handle_message,
                    [f"capability_{i % 2}"],  # Alternate capabilities
                )
                agents.append(agent)

            try:
                from src.agents.base_agent import AgentMessage, MessageType

                async def route_messages():
                    results = []
                    for i in range(20):
                        message = AgentMessage(
                            type=MessageType.TASK_REQUEST,
                            content={"routing_test": i},
                            sender_id=agents[0].agent_id,
                        )
                        result = await bus.send_message(
                            message, required_capabilities=["capability_0"]
                        )
                        results.append(result)
                    return results

                await self._run_benchmark(
                    f"routing_{strategy.value}",
                    "routing_performance",
                    route_messages,
                    iterations=5,
                )

            finally:
                for agent in agents:
                    await agent.stop()
                await bus.stop()

    async def benchmark_message_bus_reliability(self) -> None:
        """Benchmark message bus reliability features."""
        self.logger.info("Benchmarking message bus reliability")

        from src.coordination.enhanced_message_bus import DeliveryMode

        bus = EnhancedMessageBus()
        await bus.start()

        agent1 = TestAgent("reliability_sender")
        agent2 = TestAgent("reliability_receiver")

        await agent1.initialize()
        await agent2.initialize()
        await agent1.start()
        await agent2.start()

        await bus.register_agent(agent1.agent_id, agent1._handle_message, ["sender"])
        await bus.register_agent(agent2.agent_id, agent2._handle_message, ["receiver"])

        try:
            from src.agents.base_agent import AgentMessage, MessageType

            # Test different delivery modes
            delivery_modes = [DeliveryMode.FIRE_AND_FORGET, DeliveryMode.AT_LEAST_ONCE]

            for mode in delivery_modes:

                async def send_reliable_message():
                    message = AgentMessage(
                        type=MessageType.NOTIFICATION,
                        content={"reliability_test": mode.value},
                        sender_id=agent1.agent_id,
                        recipient_id=agent2.agent_id,
                    )
                    return await bus.send_message(message, delivery_mode=mode)

                await self._run_benchmark(
                    f"delivery_mode_{mode.value}",
                    "reliability_performance",
                    send_reliable_message,
                    iterations=30,
                )

        finally:
            await agent1.stop()
            await agent2.stop()
            await bus.stop()

    async def benchmark_multi_agent_coordination(self) -> None:
        """Benchmark multi-agent coordination performance."""
        self.logger.info("Benchmarking multi-agent coordination")

        bus = EnhancedMessageBus()
        await bus.start()

        # Create coordination scenario with multiple agents
        agents = []
        for i in range(6):
            agent = TestAgent(f"coord_agent_{i}")
            await agent.initialize()
            await agent.start()
            await bus.register_agent(
                agent.agent_id, agent._handle_message, ["coordination"]
            )
            agents.append(agent)

        try:
            # Benchmark coordinated task execution
            async def coordinate_tasks():
                tasks = []
                for i, agent in enumerate(agents):
                    task = {
                        "id": f"coord_task_{i}",
                        "type": "simple",
                        "coordination_id": "benchmark_coordination",
                    }
                    tasks.append(agent.process_task(task))

                return await asyncio.gather(*tasks)

            await self._run_benchmark(
                "coordinated_task_execution",
                "coordination_performance",
                coordinate_tasks,
                iterations=10,
            )

            # Benchmark agent-to-agent communication
            from src.agents.base_agent import AgentMessage, MessageType

            async def agent_communication_chain():
                results = []
                for i in range(len(agents) - 1):
                    message = AgentMessage(
                        type=MessageType.NOTIFICATION,
                        content={"chain_step": i},
                        sender_id=agents[i].agent_id,
                        recipient_id=agents[i + 1].agent_id,
                    )
                    result = await bus.send_message(message)
                    results.append(result)
                return results

            await self._run_benchmark(
                "agent_communication_chain",
                "coordination_performance",
                agent_communication_chain,
                iterations=15,
            )

        finally:
            for agent in agents:
                await agent.stop()
            await bus.stop()

    async def benchmark_resource_utilization(self) -> None:
        """Benchmark resource utilization patterns."""
        self.logger.info("Benchmarking resource utilization")

        # Create resource-intensive scenario
        agent = TestAgent("resource_test_agent")
        await agent.initialize()
        await agent.start()

        try:
            # Memory usage benchmark
            async def memory_intensive_task():
                # Create and process large data structures
                large_data = [{"id": i, "data": "x" * 1000} for i in range(1000)]

                task = {"id": "memory_test", "type": "simple", "large_data": large_data}
                return await agent.process_task(task)

            # Monitor memory during execution
            start_memory = psutil.Process().memory_info().rss

            result = await self._run_benchmark(
                "memory_intensive_processing",
                "resource_utilization",
                memory_intensive_task,
                iterations=20,
            )

            end_memory = psutil.Process().memory_info().rss

            if result:
                result.metrics["memory_delta_mb"] = (
                    (end_memory - start_memory) / 1024 / 1024
                )
                result.metrics["peak_memory_mb"] = end_memory / 1024 / 1024

            # CPU usage benchmark
            async def cpu_intensive_task():
                # Simulate CPU-intensive work
                start_time = time.time()
                total = 0
                while time.time() - start_time < 0.1:  # 100ms of work
                    total += sum(range(1000))

                task = {"id": "cpu_test", "type": "simple", "cpu_result": total}
                return await agent.process_task(task)

            await self._run_benchmark(
                "cpu_intensive_processing",
                "resource_utilization",
                cpu_intensive_task,
                iterations=10,
            )

        finally:
            await agent.stop()

    async def benchmark_scalability(self) -> None:
        """Benchmark system scalability characteristics."""
        self.logger.info("Benchmarking system scalability")

        # Test with increasing number of agents
        agent_counts = [1, 3, 5, 10]

        for agent_count in agent_counts:
            bus = EnhancedMessageBus()
            await bus.start()

            agents = []
            for i in range(agent_count):
                agent = TestAgent(f"scale_agent_{i}")
                await agent.initialize()
                await agent.start()
                await bus.register_agent(
                    agent.agent_id, agent._handle_message, ["scalability_test"]
                )
                agents.append(agent)

            try:
                # Benchmark task processing at different scales
                async def scale_test():
                    tasks = []
                    for agent in agents:
                        task = {"id": f"scale_task_{agent.agent_id}", "type": "simple"}
                        tasks.append(agent.process_task(task))

                    return await asyncio.gather(*tasks)

                result = await self._run_benchmark(
                    f"scalability_{agent_count}_agents",
                    "scalability_performance",
                    scale_test,
                    iterations=10,
                )

                if result:
                    result.metrics["agent_count"] = agent_count
                    result.metrics["tasks_per_agent"] = 1
                    result.metrics["total_tasks"] = agent_count

            finally:
                for agent in agents:
                    await agent.stop()
                await bus.stop()

    async def _run_benchmark(
        self, name: str, category: str, operation: Callable, iterations: int = 10
    ) -> Optional[BenchmarkResult]:
        """Run a single benchmark operation."""
        self.logger.debug(f"Running benchmark: {name} ({iterations} iterations)")

        start_time = time.time()
        success_count = 0
        errors = []

        try:
            for i in range(iterations):
                try:
                    await operation()
                    success_count += 1
                except Exception as e:
                    errors.append(str(e))

            duration = time.time() - start_time
            success = success_count == iterations

            result = BenchmarkResult(
                name=name,
                category=category,
                duration=duration,
                success=success,
                iterations=iterations,
                metrics={
                    "success_count": success_count,
                    "error_count": len(errors),
                    "success_rate": success_count / iterations,
                    "errors": errors[:5],  # Keep only first 5 errors
                },
            )

            self.results.append(result)
            return result

        except Exception as e:
            self.logger.error(f"Benchmark {name} failed: {e}")
            return None

    async def _run_concurrent_benchmark(
        self,
        name: str,
        category: str,
        operation: Callable,
        concurrent_count: int,
        iterations: int = 5,
    ) -> Optional[BenchmarkResult]:
        """Run benchmark with concurrent operations."""
        self.logger.debug(
            f"Running concurrent benchmark: {name} ({concurrent_count}x{iterations})"
        )

        start_time = time.time()
        total_operations = 0
        total_successes = 0

        try:
            for iteration in range(iterations):
                # Run concurrent operations
                tasks = [operation() for _ in range(concurrent_count)]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                total_operations += concurrent_count
                total_successes += sum(
                    1 for result in results if not isinstance(result, Exception)
                )

            duration = time.time() - start_time

            result = BenchmarkResult(
                name=name,
                category=category,
                duration=duration,
                success=total_successes == total_operations,
                iterations=total_operations,
                metrics={
                    "concurrent_count": concurrent_count,
                    "iteration_count": iterations,
                    "total_operations": total_operations,
                    "success_count": total_successes,
                    "success_rate": total_successes / total_operations,
                },
            )

            self.results.append(result)
            return result

        except Exception as e:
            self.logger.error(f"Concurrent benchmark {name} failed: {e}")
            return None

    def _analyze_results(self, total_time: float) -> Dict[str, Any]:
        """Analyze benchmark results and generate insights."""
        analysis = {
            "execution_summary": {
                "total_time": total_time,
                "total_benchmarks": len(self.results),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "results_by_category": {},
            "performance_insights": {},
            "detailed_results": {},
        }

        # Group results by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)

        # Analyze each category
        for category, results in categories.items():
            category_analysis = {
                "benchmark_count": len(results),
                "average_duration": statistics.mean([r.duration for r in results]),
                "average_throughput": statistics.mean([r.throughput for r in results]),
                "success_rate": statistics.mean(
                    [
                        r.metrics.get("success_rate", 1.0 if r.success else 0.0)
                        for r in results
                    ]
                ),
                "benchmarks": {
                    r.name: {
                        "duration": r.duration,
                        "throughput": r.throughput,
                        "success": r.success,
                        "metrics": r.metrics,
                    }
                    for r in results
                },
            }

            analysis["results_by_category"][category] = category_analysis

        # Generate performance insights
        if self.results:
            fastest_benchmark = min(
                self.results, key=lambda r: r.avg_time_per_operation
            )
            highest_throughput = max(self.results, key=lambda r: r.throughput)

            analysis["performance_insights"] = {
                "fastest_operation": {
                    "name": fastest_benchmark.name,
                    "avg_time_ms": fastest_benchmark.avg_time_per_operation * 1000,
                    "category": fastest_benchmark.category,
                },
                "highest_throughput": {
                    "name": highest_throughput.name,
                    "ops_per_second": highest_throughput.throughput,
                    "category": highest_throughput.category,
                },
                "overall_success_rate": statistics.mean(
                    [
                        r.metrics.get("success_rate", 1.0 if r.success else 0.0)
                        for r in self.results
                    ]
                ),
            }

        # Store detailed results
        analysis["detailed_results"] = [
            {
                "name": r.name,
                "category": r.category,
                "duration": r.duration,
                "throughput": r.throughput,
                "success": r.success,
                "iterations": r.iterations,
                "avg_time_per_operation": r.avg_time_per_operation,
                "metrics": r.metrics,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in self.results
        ]

        return analysis

    async def save_benchmark_report(self, output_path: str) -> None:
        """Save benchmark report to file."""
        analysis = self._analyze_results(0)

        report = {
            "benchmark_suite": "Enhanced Agent Systems Performance Benchmarks",
            "system_info": {
                "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}",
                "cpu_count": psutil.cpu_count(),
                "memory_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
                "platform": __import__("platform").platform(),
            },
            "configuration": self.config,
            **analysis,
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"Benchmark report saved to {output_path}")


# Convenience function for running benchmarks
async def run_performance_benchmarks(
    config: Optional[Dict[str, Any]] = None,
    save_report: bool = True,
    report_path: str = "/tmp/agent_performance_benchmark.json",
) -> Dict[str, Any]:
    """Run complete performance benchmark suite.

    Args:
        config: Benchmark configuration
        save_report: Whether to save detailed report
        report_path: Path to save report

    Returns:
        Benchmark analysis results
    """
    benchmark = PerformanceBenchmark(config)

    try:
        analysis = await benchmark.run_all_benchmarks()

        if save_report:
            await benchmark.save_benchmark_report(report_path)

        return analysis

    except Exception as e:
        logger.error(f"Performance benchmark suite failed: {e}")
        raise


if __name__ == "__main__":
    # Run benchmarks directly
    asyncio.run(run_performance_benchmarks())
