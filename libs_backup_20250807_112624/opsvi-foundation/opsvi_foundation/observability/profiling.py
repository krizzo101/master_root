"""
Performance profiling utilities.

Provides CPU profiling, memory analysis, async profiling, and performance
monitoring capabilities for identifying bottlenecks and optimizing code.
"""

from __future__ import annotations

import asyncio
import cProfile
import functools
import io
import pstats
import time
import tracemalloc
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any

from opsvi_foundation.patterns import ComponentError


class ProfilingError(ComponentError):
    """Raised when profiling operation fails."""


class ProfilingType(Enum):
    """Profiling types."""

    CPU = "cpu"
    MEMORY = "memory"
    ASYNC = "async"
    COMBINED = "combined"


@dataclass
class ProfilingResult:
    """Profiling result data."""

    profiling_type: ProfilingType
    duration: float
    function_name: str
    stats: dict[str, Any]
    memory_snapshot: dict[str, Any] | None = None
    cpu_profile: str | None = None


class CPUProfiler:
    """CPU profiling utilities."""

    def __init__(self):
        """Initialize CPU profiler."""
        self.profiler = cProfile.Profile()
        self.stats = None

    def start(self) -> None:
        """Start CPU profiling."""
        self.profiler.enable()

    def stop(self) -> pstats.Stats:
        """Stop CPU profiling and return stats."""
        self.profiler.disable()
        self.stats = pstats.Stats(self.profiler)
        return self.stats

    def get_stats_summary(self) -> dict[str, Any]:
        """Get profiling stats summary."""
        if not self.stats:
            return {}

        # Capture stats output
        output = io.StringIO()
        self.stats.stream = output
        self.stats.print_stats()
        stats_output = output.getvalue()

        # Parse key metrics
        lines = stats_output.split("\n")
        summary = {"total_calls": 0, "total_time": 0.0, "function_stats": []}

        for line in lines[3:]:  # Skip header lines
            if line.strip():
                parts = line.split()
                if len(parts) >= 6:
                    try:
                        calls = int(parts[0])
                        total_time = float(parts[1])
                        per_call = float(parts[2])
                        cumulative_time = float(parts[3])
                        function_name = " ".join(parts[5:])

                        summary["total_calls"] += calls
                        summary["total_time"] += total_time
                        summary["function_stats"].append(
                            {
                                "function": function_name,
                                "calls": calls,
                                "total_time": total_time,
                                "per_call": per_call,
                                "cumulative_time": cumulative_time,
                            },
                        )
                    except (ValueError, IndexError):
                        continue

        return summary


class MemoryProfiler:
    """Memory profiling utilities."""

    def __init__(self):
        """Initialize memory profiler."""
        self.start_snapshot = None
        self.end_snapshot = None

    def start(self) -> None:
        """Start memory profiling."""
        tracemalloc.start()
        self.start_snapshot = tracemalloc.take_snapshot()

    def stop(self) -> dict[str, Any]:
        """Stop memory profiling and return analysis."""
        if not self.start_snapshot:
            return {}

        self.end_snapshot = tracemalloc.take_snapshot()

        # Calculate memory differences
        top_stats = self.end_snapshot.compare_to(self.start_snapshot, "lineno")

        # Get current memory usage
        current, peak = tracemalloc.get_traced_memory()

        analysis = {
            "current_memory": current,
            "peak_memory": peak,
            "memory_diff": current - self.start_snapshot.statistics("filename")[0].size
            if self.start_snapshot.statistics("filename")
            else 0,
            "top_allocations": [],
        }

        # Get top memory allocations
        for stat in top_stats[:10]:  # Top 10
            analysis["top_allocations"].append(
                {
                    "filename": stat.traceback.format()[-1]
                    if stat.traceback
                    else "Unknown",
                    "size_diff": stat.size_diff,
                    "count_diff": stat.count_diff,
                },
            )

        tracemalloc.stop()
        return analysis


class AsyncProfiler:
    """Async profiling utilities."""

    def __init__(self):
        """Initialize async profiler."""
        self.start_time = None
        self.end_time = None
        self.tasks = []
        self.task_stats = {}

    def start(self) -> None:
        """Start async profiling."""
        self.start_time = time.time()
        self.tasks = []
        self.task_stats = {}

    def stop(self) -> dict[str, Any]:
        """Stop async profiling and return analysis."""
        if not self.start_time:
            return {}

        self.end_time = time.time()
        duration = self.end_time - self.start_time

        # Get current event loop stats
        loop = asyncio.get_event_loop()

        analysis = {
            "duration": duration,
            "total_tasks": len(asyncio.all_tasks(loop)),
            "running_tasks": len([t for t in asyncio.all_tasks(loop) if not t.done()]),
            "completed_tasks": len([t for t in asyncio.all_tasks(loop) if t.done()]),
            "task_stats": self.task_stats,
        }

        return analysis

    def track_task(self, task: asyncio.Task) -> None:
        """Track an async task."""
        task_name = getattr(task, "_name", f"Task-{id(task)}")
        self.task_stats[task_name] = {"created_at": time.time(), "status": task._state}


class PerformanceProfiler:
    """Main performance profiler combining CPU, memory, and async profiling."""

    def __init__(self):
        """Initialize performance profiler."""
        self.cpu_profiler = CPUProfiler()
        self.memory_profiler = MemoryProfiler()
        self.async_profiler = AsyncProfiler()
        self.active = False

    def start(self, profiling_type: ProfilingType = ProfilingType.COMBINED) -> None:
        """
        Start profiling.

        Args:
            profiling_type: Type of profiling to perform
        """
        self.active = True

        if profiling_type in [ProfilingType.CPU, ProfilingType.COMBINED]:
            self.cpu_profiler.start()

        if profiling_type in [ProfilingType.MEMORY, ProfilingType.COMBINED]:
            self.memory_profiler.start()

        if profiling_type in [ProfilingType.ASYNC, ProfilingType.COMBINED]:
            self.async_profiler.start()

    def stop(
        self,
        profiling_type: ProfilingType = ProfilingType.COMBINED,
    ) -> ProfilingResult:
        """
        Stop profiling and return results.

        Args:
            profiling_type: Type of profiling to stop

        Returns:
            Profiling result
        """
        if not self.active:
            raise ProfilingError("Profiling not started")

        self.active = False
        duration = time.time()

        # Stop profilers
        cpu_stats = None
        memory_stats = None
        async_stats = None

        if profiling_type in [ProfilingType.CPU, ProfilingType.COMBINED]:
            cpu_stats = self.cpu_profiler.stop()

        if profiling_type in [ProfilingType.MEMORY, ProfilingType.COMBINED]:
            memory_stats = self.memory_profiler.stop()

        if profiling_type in [ProfilingType.ASYNC, ProfilingType.COMBINED]:
            async_stats = self.async_profiler.stop()

        # Combine results
        combined_stats = {
            "cpu": cpu_stats.get_stats_summary() if cpu_stats else None,
            "memory": memory_stats,
            "async": async_stats,
        }

        return ProfilingResult(
            profiling_type=profiling_type,
            duration=duration,
            function_name="",
            stats=combined_stats,
            memory_snapshot=memory_stats,
            cpu_profile=str(cpu_stats) if cpu_stats else None,
        )


class ProfilingManager:
    """Manager for multiple profilers."""

    def __init__(self):
        """Initialize profiling manager."""
        self.profilers: dict[str, PerformanceProfiler] = {}
        self.results: dict[str, list[ProfilingResult]] = {}

    def create_profiler(self, name: str) -> PerformanceProfiler:
        """
        Create a new profiler.

        Args:
            name: Profiler name

        Returns:
            Created profiler
        """
        profiler = PerformanceProfiler()
        self.profilers[name] = profiler
        self.results[name] = []
        return profiler

    def get_profiler(self, name: str) -> PerformanceProfiler | None:
        """Get profiler by name."""
        return self.profilers.get(name)

    def start_profiling(
        self,
        name: str,
        profiling_type: ProfilingType = ProfilingType.COMBINED,
    ) -> None:
        """
        Start profiling with named profiler.

        Args:
            name: Profiler name
            profiling_type: Type of profiling
        """
        profiler = self.get_profiler(name)
        if not profiler:
            profiler = self.create_profiler(name)

        profiler.start(profiling_type)

    def stop_profiling(
        self,
        name: str,
        profiling_type: ProfilingType = ProfilingType.COMBINED,
    ) -> ProfilingResult:
        """
        Stop profiling with named profiler.

        Args:
            name: Profiler name
            profiling_type: Type of profiling

        Returns:
            Profiling result
        """
        profiler = self.get_profiler(name)
        if not profiler:
            raise ProfilingError(f"Profiler '{name}' not found")

        result = profiler.stop(profiling_type)
        self.results[name].append(result)
        return result

    def get_results(self, name: str) -> list[ProfilingResult]:
        """Get profiling results for named profiler."""
        return self.results.get(name, [])

    def clear_results(self, name: str) -> None:
        """Clear profiling results for named profiler."""
        if name in self.results:
            self.results[name].clear()


# Global profiling manager
profiling_manager = ProfilingManager()


@contextmanager
def profile_function(
    name: str,
    profiling_type: ProfilingType = ProfilingType.COMBINED,
    profiler_name: str = "default",
):
    """
    Context manager for profiling functions.

    Args:
        name: Profiling session name
        profiling_type: Type of profiling
        profiler_name: Profiler name
    """
    profiling_manager.start_profiling(profiler_name, profiling_type)
    try:
        yield
    finally:
        result = profiling_manager.stop_profiling(profiler_name, profiling_type)
        result.function_name = name


@asynccontextmanager
async def async_profile_function(
    name: str,
    profiling_type: ProfilingType = ProfilingType.COMBINED,
    profiler_name: str = "default",
):
    """
    Async context manager for profiling async functions.

    Args:
        name: Profiling session name
        profiling_type: Type of profiling
        profiler_name: Profiler name
    """
    profiling_manager.start_profiling(profiler_name, profiling_type)
    try:
        yield
    finally:
        result = profiling_manager.stop_profiling(profiler_name, profiling_type)
        result.function_name = name


def profile_decorator(
    profiling_type: ProfilingType = ProfilingType.COMBINED,
    profiler_name: str = "default",
):
    """
    Decorator for profiling functions.

    Args:
        profiling_type: Type of profiling
        profiler_name: Profiler name
    """

    def decorator(func):
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                async with async_profile_function(
                    f"{func.__module__}.{func.__name__}",
                    profiling_type,
                    profiler_name,
                ):
                    return await func(*args, **kwargs)

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with profile_function(
                f"{func.__module__}.{func.__name__}",
                profiling_type,
                profiler_name,
            ):
                return func(*args, **kwargs)

        return sync_wrapper

    return decorator


class PerformanceMonitor:
    """Continuous performance monitoring."""

    def __init__(self, interval: float = 60.0):
        """
        Initialize performance monitor.

        Args:
            interval: Monitoring interval in seconds
        """
        self.interval = interval
        self.monitoring = False
        self.metrics: list[dict[str, Any]] = []
        self._monitor_task: asyncio.Task | None = None

    async def start_monitoring(self) -> None:
        """Start continuous monitoring."""
        if self.monitoring:
            return

        self.monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self) -> None:
        """Stop continuous monitoring."""
        self.monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while self.monitoring:
            try:
                # Collect system metrics
                import psutil

                metric = {
                    "timestamp": time.time(),
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage("/").percent,
                    "network_io": psutil.net_io_counters()._asdict(),
                    "process_count": len(psutil.pids()),
                }

                self.metrics.append(metric)

                # Keep only last 1000 metrics
                if len(self.metrics) > 1000:
                    self.metrics = self.metrics[-1000:]

                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Performance monitoring error: {e}")
                await asyncio.sleep(self.interval)

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get metrics summary."""
        if not self.metrics:
            return {}

        recent_metrics = self.metrics[-100:]  # Last 100 metrics

        summary = {
            "total_metrics": len(self.metrics),
            "monitoring_duration": self.metrics[-1]["timestamp"]
            - self.metrics[0]["timestamp"]
            if len(self.metrics) > 1
            else 0,
            "average_cpu": sum(m["cpu_percent"] for m in recent_metrics)
            / len(recent_metrics),
            "average_memory": sum(m["memory_percent"] for m in recent_metrics)
            / len(recent_metrics),
            "average_disk": sum(m["disk_usage"] for m in recent_metrics)
            / len(recent_metrics),
            "max_cpu": max(m["cpu_percent"] for m in recent_metrics),
            "max_memory": max(m["memory_percent"] for m in recent_metrics),
            "max_disk": max(m["disk_usage"] for m in recent_metrics),
        }

        return summary


# Global performance monitor
performance_monitor = PerformanceMonitor()
