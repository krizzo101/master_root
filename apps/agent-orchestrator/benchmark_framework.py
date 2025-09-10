#!/usr/bin/env python3
"""
Framework Performance Benchmark - Measures orchestrator overhead without actual Claude execution
"""

import asyncio
import gc
import json
import os
import random
import sys
import tempfile
import threading
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import psutil

# Add orchestrator src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


class MockOrchestrator:
    """Mock orchestrator for benchmarking framework overhead"""

    def __init__(self, max_parallel: int = 5):
        self.max_parallel = max_parallel
        self.semaphore = asyncio.Semaphore(max_parallel)
        self.token_pool = MockTokenPool(
            ["token_" + str(i) for i in range(max_parallel)]
        )
        self.metrics = {
            "tasks_processed": 0,
            "tasks_queued": 0,
            "active_tasks": 0,
            "token_acquisitions": 0,
            "token_releases": 0,
        }
        self.lock = threading.Lock()

    async def execute_task(self, task_id: str, delay: float = 0.1):
        """Simulate task execution with controlled delay"""
        async with self.semaphore:
            with self.lock:
                self.metrics["active_tasks"] += 1
                self.metrics["tasks_queued"] -= 1

            # Simulate token acquisition
            token_idx = await self.token_pool.acquire()
            self.metrics["token_acquisitions"] += 1

            # Simulate work
            await asyncio.sleep(delay)

            # Release token
            await self.token_pool.release(token_idx)
            self.metrics["token_releases"] += 1

            with self.lock:
                self.metrics["active_tasks"] -= 1
                self.metrics["tasks_processed"] += 1

            return {"task_id": task_id, "status": "completed"}

    async def execute_batch(self, num_tasks: int, task_delay: float = 0.1):
        """Execute batch of tasks"""
        tasks = []
        for i in range(num_tasks):
            with self.lock:
                self.metrics["tasks_queued"] += 1
            tasks.append(self.execute_task(f"task_{i}", task_delay))

        results = await asyncio.gather(*tasks)
        return results


class MockTokenPool:
    """Mock token pool for benchmarking contention"""

    def __init__(self, tokens: List[str]):
        self.tokens = tokens
        self.available = asyncio.Queue()
        for i, token in enumerate(tokens):
            self.available.put_nowait(i)
        self.wait_times = []
        self.acquisition_count = 0
        self.contention_count = 0

    async def acquire(self):
        """Acquire a token with wait time tracking"""
        start = time.time()

        # Check if we need to wait (contention)
        if self.available.empty():
            self.contention_count += 1

        token_idx = await self.available.get()
        wait_time = time.time() - start
        self.wait_times.append(wait_time)
        self.acquisition_count += 1
        return token_idx

    async def release(self, token_idx: int):
        """Release a token"""
        await self.available.put(token_idx)


class PerformanceProfiler:
    """Main performance profiling class"""

    def __init__(self):
        self.results = {}
        self.process = psutil.Process()

    def measure_task_throughput(
        self, task_counts: List[int], parallelism_levels: List[int]
    ) -> Dict:
        """Measure task throughput at various scales"""
        print("\n🔬 MEASURING TASK THROUGHPUT")
        print("-" * 40)

        throughput_results = []

        for task_count in task_counts:
            for parallelism in parallelism_levels:
                orchestrator = MockOrchestrator(max_parallel=parallelism)

                start_time = time.time()
                start_memory = self.process.memory_info().rss / (1024 * 1024)  # MB

                # Run async tasks
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    orchestrator.execute_batch(task_count, task_delay=0.05)
                )
                loop.close()

                elapsed = time.time() - start_time
                end_memory = self.process.memory_info().rss / (1024 * 1024)  # MB

                result = {
                    "task_count": task_count,
                    "parallelism": parallelism,
                    "total_time_sec": round(elapsed, 3),
                    "throughput_tasks_per_sec": round(task_count / elapsed, 2),
                    "memory_delta_mb": round(end_memory - start_memory, 2),
                    "metrics": orchestrator.metrics,
                }

                throughput_results.append(result)
                print(
                    f"Tasks: {task_count:4d} | Parallel: {parallelism:2d} | "
                    f"Time: {elapsed:6.2f}s | Throughput: {result['throughput_tasks_per_sec']:7.2f} t/s"
                )

        self.results["task_throughput"] = throughput_results
        return throughput_results

    def measure_memory_per_agent(self, num_agents: int = 20) -> Dict:
        """Measure memory overhead per agent"""
        print("\n🔬 MEASURING MEMORY PER AGENT")
        print("-" * 40)

        gc.collect()
        tracemalloc.start()

        agent_memories = []

        for i in range(num_agents):
            snapshot_before = tracemalloc.take_snapshot()

            # Create mock agent with state
            agent = {
                "id": f"agent_{i}",
                "state": {"buffer": [0] * 10000},  # 10K integers
                "history": ["message"] * 100,
                "context": {"data": "x" * 1000},
            }

            snapshot_after = tracemalloc.take_snapshot()
            top_stats = snapshot_after.compare_to(snapshot_before, "lineno")

            total_memory = sum(stat.size_diff for stat in top_stats) / 1024  # KB
            agent_memories.append(total_memory)

            if i % 5 == 0:
                print(f"Agent {i:3d}: {total_memory:8.2f} KB")

        tracemalloc.stop()

        result = {
            "num_agents": num_agents,
            "avg_memory_kb": round(sum(agent_memories) / len(agent_memories), 2),
            "max_memory_kb": round(max(agent_memories), 2),
            "min_memory_kb": round(min(agent_memories), 2),
            "total_memory_mb": round(sum(agent_memories) / 1024, 2),
        }

        print(f"\nAverage per agent: {result['avg_memory_kb']:.2f} KB")

        self.results["memory_usage"] = result
        return result

    def measure_token_pool_contention(self, scenarios: List[Dict]) -> Dict:
        """Measure token pool contention under various loads"""
        print("\n🔬 MEASURING TOKEN POOL CONTENTION")
        print("-" * 40)

        contention_results = []

        for scenario in scenarios:
            num_tasks = scenario["tasks"]
            num_tokens = scenario["tokens"]

            token_pool = MockTokenPool([f"token_{i}" for i in range(num_tokens)])

            async def simulate_contention():
                tasks = []
                for i in range(num_tasks):

                    async def acquire_and_work():
                        token = await token_pool.acquire()
                        await asyncio.sleep(random.uniform(0.01, 0.05))
                        await token_pool.release(token)

                    tasks.append(acquire_and_work())

                await asyncio.gather(*tasks)

            start = time.time()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(simulate_contention())
            loop.close()
            elapsed = time.time() - start

            avg_wait = (
                sum(token_pool.wait_times) / len(token_pool.wait_times)
                if token_pool.wait_times
                else 0
            )

            result = {
                "tasks": num_tasks,
                "tokens": num_tokens,
                "contention_ratio": round(num_tasks / num_tokens, 2),
                "total_time_sec": round(elapsed, 3),
                "avg_wait_time_ms": round(avg_wait * 1000, 2),
                "max_wait_time_ms": round(max(token_pool.wait_times) * 1000, 2)
                if token_pool.wait_times
                else 0,
                "contention_events": token_pool.contention_count,
                "contention_rate": round(
                    token_pool.contention_count / num_tasks * 100, 1
                ),
            }

            contention_results.append(result)
            print(
                f"Tasks: {num_tasks:3d} | Tokens: {num_tokens:2d} | "
                f"Contention: {result['contention_rate']:5.1f}% | "
                f"Avg Wait: {result['avg_wait_time_ms']:6.2f}ms"
            )

        self.results["token_pool_contention"] = contention_results
        return contention_results

    def measure_file_io_latency(self, operations: int = 100) -> Dict:
        """Measure file I/O performance"""
        print("\n🔬 MEASURING FILE I/O LATENCY")
        print("-" * 40)

        io_results = {}
        sizes = [1024, 10240, 102400, 1048576]  # 1KB, 10KB, 100KB, 1MB

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            for size in sizes:
                data = os.urandom(size)
                write_times = []
                read_times = []

                for i in range(operations):
                    file_path = temp_path / f"test_{i}.dat"

                    # Write
                    start = time.time()
                    with open(file_path, "wb") as f:
                        f.write(data)
                        f.flush()
                        os.fsync(f.fileno())
                    write_times.append(time.time() - start)

                    # Read
                    start = time.time()
                    with open(file_path, "rb") as f:
                        _ = f.read()
                    read_times.append(time.time() - start)

                    file_path.unlink()

                size_label = (
                    f"{size // 1024}KB" if size < 1048576 else f"{size // 1048576}MB"
                )

                io_results[size_label] = {
                    "size_bytes": size,
                    "operations": operations,
                    "avg_write_ms": round(
                        sum(write_times) / len(write_times) * 1000, 3
                    ),
                    "avg_read_ms": round(sum(read_times) / len(read_times) * 1000, 3),
                    "write_throughput_mb_s": round(
                        size * operations / (sum(write_times) * 1048576), 2
                    ),
                    "read_throughput_mb_s": round(
                        size * operations / (sum(read_times) * 1048576), 2
                    ),
                }

                print(
                    f"{size_label:5s}: Write {io_results[size_label]['avg_write_ms']:6.2f}ms | "
                    f"Read {io_results[size_label]['avg_read_ms']:6.2f}ms | "
                    f"Throughput W:{io_results[size_label]['write_throughput_mb_s']:6.1f} R:{io_results[size_label]['read_throughput_mb_s']:6.1f} MB/s"
                )

        self.results["file_io_latency"] = io_results
        return io_results

    def run_comprehensive_benchmark(self) -> Dict:
        """Run all benchmarks"""
        print("=" * 50)
        print("🚀 ORCHESTRATOR PERFORMANCE BENCHMARK")
        print("=" * 50)

        # System info
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)

        print(f"\n📊 System: {cpu_count} CPUs, {memory_gb:.1f}GB RAM")
        print(f"📅 Timestamp: {datetime.now().isoformat()}")

        # Run benchmarks
        self.measure_task_throughput(
            task_counts=[10, 50, 100, 200], parallelism_levels=[1, 3, 5, 10]
        )

        self.measure_memory_per_agent(num_agents=20)

        self.measure_token_pool_contention(
            [
                {"tasks": 10, "tokens": 5},
                {"tasks": 20, "tokens": 5},
                {"tasks": 50, "tokens": 5},
                {"tasks": 50, "tokens": 10},
                {"tasks": 100, "tokens": 10},
            ]
        )

        self.measure_file_io_latency(operations=50)

        # Calculate summary metrics
        throughput_data = self.results["task_throughput"]
        best_throughput = max(
            throughput_data, key=lambda x: x["throughput_tasks_per_sec"]
        )

        self.results["summary"] = {
            "timestamp": datetime.now().isoformat(),
            "system": {"cpus": cpu_count, "memory_gb": round(memory_gb, 1)},
            "peak_performance": {
                "throughput_tasks_per_sec": best_throughput["throughput_tasks_per_sec"],
                "optimal_parallelism": best_throughput["parallelism"],
                "at_task_count": best_throughput["task_count"],
            },
            "memory": {
                "avg_per_agent_kb": self.results["memory_usage"]["avg_memory_kb"],
                "total_20_agents_mb": self.results["memory_usage"]["total_memory_mb"],
            },
            "token_pool": {
                "max_contention_rate": max(
                    r["contention_rate"] for r in self.results["token_pool_contention"]
                ),
                "avg_wait_under_contention_ms": sum(
                    r["avg_wait_time_ms"] for r in self.results["token_pool_contention"]
                )
                / len(self.results["token_pool_contention"]),
            },
            "file_io": {
                "best_write_throughput_mb_s": max(
                    v["write_throughput_mb_s"]
                    for v in self.results["file_io_latency"].values()
                ),
                "best_read_throughput_mb_s": max(
                    v["read_throughput_mb_s"]
                    for v in self.results["file_io_latency"].values()
                ),
            },
        }

        # Save results
        output_file = Path("baseline_metrics.json")
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print("\n" + "=" * 50)
        print("✅ BENCHMARK COMPLETE")
        print(f"📁 Results saved to: {output_file}")
        print("\n📈 SUMMARY:")
        print(
            f"   Peak Throughput: {self.results['summary']['peak_performance']['throughput_tasks_per_sec']} tasks/sec"
        )
        print(
            f"   Optimal Parallelism: {self.results['summary']['peak_performance']['optimal_parallelism']}"
        )
        print(
            f"   Memory per Agent: {self.results['summary']['memory']['avg_per_agent_kb']} KB"
        )
        print(
            f"   Max Token Contention: {self.results['summary']['token_pool']['max_contention_rate']}%"
        )
        print(
            f"   File I/O: Write {self.results['summary']['file_io']['best_write_throughput_mb_s']} MB/s, Read {self.results['summary']['file_io']['best_read_throughput_mb_s']} MB/s"
        )
        print("=" * 50)

        return self.results


if __name__ == "__main__":
    profiler = PerformanceProfiler()
    results = profiler.run_comprehensive_benchmark()
