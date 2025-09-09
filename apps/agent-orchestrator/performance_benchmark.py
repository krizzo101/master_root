#!/usr/bin/env python3
"""
Comprehensive Performance Benchmark Suite for Agent-Orchestrator
Measures: task throughput, memory usage per agent, token pool contention, file I/O latency
"""

import asyncio
import gc
import hashlib
import json
import os
import random
import sys
import tempfile
import time
import tracemalloc
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

# Add orchestrator src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from enhanced_token_pool import EnhancedTokenPool
from generic_orchestrator import AgentTask, GenericOrchestrator, TokenPool
from monitoring.metrics_collector import MetricsCollector


class PerformanceBenchmark:
    """Comprehensive performance benchmarking for orchestrator"""

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("./benchmark_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.metrics = {
            "task_throughput": {},
            "memory_usage": {},
            "token_pool_contention": {},
            "file_io_latency": {},
            "agent_execution_times": {},
            "system_resources": {},
            "concurrency_metrics": {},
        }

        self.process = psutil.Process()

    async def benchmark_task_throughput(
        self, num_tasks: int = 50, parallelism: int = 5
    ) -> Dict[str, Any]:
        """Measure task throughput with varying loads"""
        print(
            f"\n📊 Benchmarking Task Throughput ({num_tasks} tasks, {parallelism} parallel)..."
        )

        # Create test tasks
        tasks = []
        for i in range(num_tasks):
            task = AgentTask(
                task_id=f"perf_test_{i}",
                task_type="test_task",
                prompt=f"Simple test task {i}: Count to 10 and return done.",
                context={"iteration": i},
            )
            tasks.append(task)

        # Measure throughput with orchestrator
        start_time = time.time()
        start_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        try:
            # Create orchestrator with limited parallelism
            orchestrator = GenericOrchestrator(
                output_dir=self.output_dir
                / f"throughput_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                max_parallel=parallelism,
            )

            # Track individual task times
            task_times = []
            completed_tasks = 0
            failed_tasks = 0

            # Execute tasks
            results = await orchestrator.execute_tasks(tasks)

            for task_id, result in results.items():
                if result.get("status") == "completed":
                    completed_tasks += 1
                    if result.get("start_time") and result.get("end_time"):
                        task_times.append(result["end_time"] - result["start_time"])
                else:
                    failed_tasks += 1

        except Exception as e:
            print(f"❌ Throughput benchmark failed: {e}")
            return {"error": str(e)}

        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        total_time = end_time - start_time
        throughput_tasks_per_second = num_tasks / total_time if total_time > 0 else 0
        memory_delta = end_memory - start_memory

        metrics = {
            "total_tasks": num_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "parallelism": parallelism,
            "total_time_seconds": round(total_time, 3),
            "throughput_tasks_per_second": round(throughput_tasks_per_second, 3),
            "average_task_time": round(sum(task_times) / len(task_times), 3)
            if task_times
            else 0,
            "min_task_time": round(min(task_times), 3) if task_times else 0,
            "max_task_time": round(max(task_times), 3) if task_times else 0,
            "memory_used_mb": round(memory_delta, 2),
            "success_rate": round((completed_tasks / num_tasks) * 100, 2)
            if num_tasks > 0
            else 0,
        }

        self.metrics["task_throughput"] = metrics
        print(f"✅ Throughput: {metrics['throughput_tasks_per_second']} tasks/sec")
        print(f"   Success rate: {metrics['success_rate']}%")
        return metrics

    async def benchmark_memory_usage_per_agent(
        self, num_agents: int = 10
    ) -> Dict[str, Any]:
        """Measure memory usage per agent"""
        print(f"\n📊 Benchmarking Memory Usage ({num_agents} agents)...")

        agent_memories = []

        for i in range(num_agents):
            # Force garbage collection before measurement
            gc.collect()

            # Measure memory before agent creation
            tracemalloc.start()
            start_memory = tracemalloc.get_traced_memory()[0]

            # Create agent task
            task = AgentTask(
                task_id=f"memory_test_{i}",
                task_type="memory_test",
                prompt=f"Memory test {i}: Generate a list of 1000 random numbers and calculate their sum.",
                context={"agent_id": i},
            )

            # Execute single agent task
            orchestrator = GenericOrchestrator(
                output_dir=self.output_dir / f"memory_test_{i}", max_parallel=1
            )

            try:
                await orchestrator.execute_tasks([task])
            except:
                pass  # We're measuring memory, not success

            # Measure memory after execution
            end_memory = tracemalloc.get_traced_memory()[0]
            memory_used = (end_memory - start_memory) / 1024 / 1024  # Convert to MB

            agent_memories.append(memory_used)
            tracemalloc.stop()

            print(f"   Agent {i}: {memory_used:.2f} MB")

        metrics = {
            "num_agents": num_agents,
            "average_memory_mb": round(sum(agent_memories) / len(agent_memories), 2)
            if agent_memories
            else 0,
            "min_memory_mb": round(min(agent_memories), 2) if agent_memories else 0,
            "max_memory_mb": round(max(agent_memories), 2) if agent_memories else 0,
            "total_memory_mb": round(sum(agent_memories), 2),
            "per_agent_details": [round(m, 2) for m in agent_memories],
        }

        self.metrics["memory_usage"] = metrics
        print(f"✅ Average memory per agent: {metrics['average_memory_mb']} MB")
        return metrics

    async def benchmark_token_pool_contention(
        self, num_concurrent: int = 20, num_tokens: int = 5
    ) -> Dict[str, Any]:
        """Measure token pool contention and wait times"""
        print(
            f"\n📊 Benchmarking Token Pool Contention ({num_concurrent} concurrent, {num_tokens} tokens)..."
        )

        # Create mock tokens
        tokens = [f"test_token_{i}" for i in range(num_tokens)]

        # Create enhanced token pool for monitoring
        token_pool = EnhancedTokenPool(tokens=tokens, output_dir=self.output_dir)

        acquisition_times = []
        wait_times = []
        contention_events = []

        async def acquire_and_release(task_id: int):
            """Simulate token acquisition and release"""
            start_wait = time.time()

            # Try to acquire token
            token_index = await token_pool.acquire()

            wait_time = time.time() - start_wait
            wait_times.append(wait_time)

            if wait_time > 0.1:  # Consider >100ms as contention
                contention_events.append({"task_id": task_id, "wait_time": wait_time})

            # Simulate work
            work_time = random.uniform(0.1, 0.5)
            await asyncio.sleep(work_time)

            # Release token
            await token_pool.release(token_index)

            acquisition_times.append(wait_time + work_time)

        # Run concurrent token acquisitions
        start_time = time.time()
        tasks = [acquire_and_release(i) for i in range(num_concurrent)]
        await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        metrics = {
            "num_concurrent_requests": num_concurrent,
            "num_tokens": num_tokens,
            "contention_ratio": num_concurrent / num_tokens,
            "total_time_seconds": round(total_time, 3),
            "average_wait_time_ms": round(sum(wait_times) * 1000 / len(wait_times), 2)
            if wait_times
            else 0,
            "max_wait_time_ms": round(max(wait_times) * 1000, 2) if wait_times else 0,
            "min_wait_time_ms": round(min(wait_times) * 1000, 2) if wait_times else 0,
            "contention_events": len(contention_events),
            "contention_percentage": round(
                (len(contention_events) / num_concurrent) * 100, 2
            ),
            "throughput_per_token": round(
                num_concurrent / (total_time * num_tokens), 3
            ),
        }

        self.metrics["token_pool_contention"] = metrics
        print(f"✅ Average wait time: {metrics['average_wait_time_ms']} ms")
        print(
            f"   Contention events: {metrics['contention_events']} ({metrics['contention_percentage']}%)"
        )
        return metrics

    async def benchmark_file_io_latency(
        self, num_operations: int = 100, file_sizes: List[int] = None
    ) -> Dict[str, Any]:
        """Measure file I/O latency for various operations"""
        print(f"\n📊 Benchmarking File I/O Latency ({num_operations} operations)...")

        if file_sizes is None:
            file_sizes = [1024, 10240, 102400]  # 1KB, 10KB, 100KB

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            io_metrics = {}

            for size in file_sizes:
                write_times = []
                read_times = []

                # Generate test data
                test_data = os.urandom(size)

                for i in range(num_operations):
                    file_path = temp_path / f"test_{size}_{i}.bin"

                    # Measure write time
                    start_write = time.time()
                    with open(file_path, "wb") as f:
                        f.write(test_data)
                        f.flush()
                        os.fsync(f.fileno())
                    write_time = time.time() - start_write
                    write_times.append(write_time)

                    # Measure read time
                    start_read = time.time()
                    with open(file_path, "rb") as f:
                        _ = f.read()
                    read_time = time.time() - start_read
                    read_times.append(read_time)

                    # Clean up
                    file_path.unlink()

                size_label = f"{size // 1024}KB"
                io_metrics[size_label] = {
                    "file_size_bytes": size,
                    "num_operations": num_operations,
                    "avg_write_ms": round(
                        sum(write_times) * 1000 / len(write_times), 3
                    ),
                    "max_write_ms": round(max(write_times) * 1000, 3),
                    "min_write_ms": round(min(write_times) * 1000, 3),
                    "avg_read_ms": round(sum(read_times) * 1000 / len(read_times), 3),
                    "max_read_ms": round(max(read_times) * 1000, 3),
                    "min_read_ms": round(min(read_times) * 1000, 3),
                    "write_throughput_mb_s": round(
                        size * num_operations / (sum(write_times) * 1024 * 1024), 2
                    ),
                    "read_throughput_mb_s": round(
                        size * num_operations / (sum(read_times) * 1024 * 1024), 2
                    ),
                }

                print(
                    f"   {size_label}: Write {io_metrics[size_label]['avg_write_ms']}ms, Read {io_metrics[size_label]['avg_read_ms']}ms"
                )

        self.metrics["file_io_latency"] = io_metrics
        return io_metrics

    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system resource metrics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count(),
                "count_physical": psutil.cpu_count(logical=False),
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent": memory.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": disk.percent,
            },
            "process": {
                "pid": self.process.pid,
                "memory_mb": round(self.process.memory_info().rss / (1024**2), 2),
                "cpu_percent": self.process.cpu_percent(),
            },
        }

        self.metrics["system_resources"] = metrics
        return metrics

    async def run_full_benchmark(self) -> Dict[str, Any]:
        """Run complete benchmark suite"""
        print("=" * 60)
        print("🚀 Starting Comprehensive Performance Benchmark")
        print("=" * 60)

        # Collect initial system metrics
        self.collect_system_metrics()

        # Run benchmarks
        await self.benchmark_task_throughput(num_tasks=30, parallelism=5)
        await self.benchmark_memory_usage_per_agent(num_agents=5)
        await self.benchmark_token_pool_contention(num_concurrent=15, num_tokens=3)
        await self.benchmark_file_io_latency(num_operations=50)

        # Test different concurrency levels
        print("\n📊 Testing Concurrency Scaling...")
        concurrency_results = []
        for parallelism in [1, 3, 5, 10]:
            result = await self.benchmark_task_throughput(
                num_tasks=20, parallelism=parallelism
            )
            concurrency_results.append(
                {
                    "parallelism": parallelism,
                    "throughput": result.get("throughput_tasks_per_second", 0),
                    "avg_time": result.get("average_task_time", 0),
                    "memory_mb": result.get("memory_used_mb", 0),
                }
            )

        self.metrics["concurrency_metrics"] = {
            "scaling_tests": concurrency_results,
            "optimal_parallelism": max(
                concurrency_results, key=lambda x: x["throughput"]
            )["parallelism"],
        }

        # Final system metrics
        final_system = self.collect_system_metrics()

        # Calculate summary
        self.metrics["summary"] = {
            "benchmark_timestamp": datetime.now().isoformat(),
            "total_benchmark_time": time.time()
            - time.mktime(datetime.now().timetuple()),
            "peak_throughput_tasks_sec": self.metrics["task_throughput"].get(
                "throughput_tasks_per_second", 0
            ),
            "avg_memory_per_agent_mb": self.metrics["memory_usage"].get(
                "average_memory_mb", 0
            ),
            "avg_token_wait_ms": self.metrics["token_pool_contention"].get(
                "average_wait_time_ms", 0
            ),
            "file_io_write_throughput_mb_s": max(
                [
                    v.get("write_throughput_mb_s", 0)
                    for v in self.metrics["file_io_latency"].values()
                ]
            )
            if self.metrics["file_io_latency"]
            else 0,
            "optimal_parallelism": self.metrics["concurrency_metrics"].get(
                "optimal_parallelism", 5
            ),
        }

        # Save results
        output_file = Path("baseline_metrics.json")
        with open(output_file, "w") as f:
            json.dump(self.metrics, f, indent=2)

        print("\n" + "=" * 60)
        print("✅ Benchmark Complete!")
        print(f"📁 Results saved to: {output_file}")
        print("\n📊 Summary:")
        for key, value in self.metrics["summary"].items():
            print(f"   {key}: {value}")
        print("=" * 60)

        return self.metrics


async def main():
    """Main benchmark execution"""
    benchmark = PerformanceBenchmark()
    results = await benchmark.run_full_benchmark()
    return results


if __name__ == "__main__":
    # Run async benchmark
    results = asyncio.run(main())
