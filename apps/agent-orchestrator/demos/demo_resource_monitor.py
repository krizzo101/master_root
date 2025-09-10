#!/usr/bin/env python3
"""
Demonstration of ResourceMonitor capabilities
Shows resource tracking, limit enforcement, and automatic task management
"""

import asyncio
import logging
import multiprocessing
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from monitoring.resource_monitor import (
    ResourceLimitAction,
    ResourceLimits,
    ResourceMonitor,
    TaskState,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def memory_intensive_task(limit_mb: int = 512):
    """Simulate a memory-intensive task"""
    print(f"\n{'='*60}")
    print(f"Starting memory-intensive task (limit: {limit_mb}MB)")
    print(f"{'='*60}")

    monitor = ResourceMonitor()
    limits = ResourceLimits(
        max_memory_mb=limit_mb,
        memory_limit_action=ResourceLimitAction.WARN,
        memory_grace_period=2.0,
    )

    # Register task
    usage = monitor.register_task("memory_task", limits=limits)
    monitor.start_monitoring()

    # Allocate memory incrementally
    data = []
    try:
        for i in range(20):
            # Allocate 50MB chunks
            chunk = bytearray(50 * 1024 * 1024)
            data.append(chunk)

            print(f"Iteration {i+1}: Allocated {(i+1)*50}MB")
            print(f"  Current: {usage.current_memory_mb:.1f}MB")
            print(f"  Peak: {usage.peak_memory_mb:.1f}MB")
            print(f"  Violations: {usage.memory_violations}")

            time.sleep(0.5)

            # Check if we should stop
            if usage.memory_violations > 5:
                print("\n⚠️  Too many memory violations, stopping task")
                break

    except MemoryError:
        print("\n❌ Memory allocation failed!")

    finally:
        monitor.stop_monitoring()
        monitor.unregister_task("memory_task")

        print(f"\n📊 Final Statistics:")
        print(f"  Peak Memory: {usage.peak_memory_mb:.1f}MB")
        print(f"  Average Memory: {usage.avg_memory_mb:.1f}MB")
        print(f"  Memory Violations: {usage.memory_violations}")
        print(f"  Task Duration: {usage.duration:.2f}s")


def cpu_intensive_task(limit_percent: float = 150):
    """Simulate a CPU-intensive task with throttling"""
    print(f"\n{'='*60}")
    print(f"Starting CPU-intensive task (limit: {limit_percent}%)")
    print(f"{'='*60}")

    monitor = ResourceMonitor(check_interval=0.5)
    limits = ResourceLimits(
        max_cpu_percent=limit_percent,
        cpu_limit_action=ResourceLimitAction.THROTTLE,
        cpu_grace_period=3.0,
    )

    # Register task
    usage = monitor.register_task("cpu_task", limits=limits)
    monitor.start_monitoring()

    # CPU-intensive work
    start_time = time.time()
    iteration = 0

    try:
        while time.time() - start_time < 10:  # Run for 10 seconds
            # Intensive computation
            result = sum(i**2 for i in range(100000))
            iteration += 1

            if iteration % 100 == 0:
                print(f"Iteration {iteration}:")
                print(f"  CPU: {usage.current_cpu_percent:.1f}%")
                print(f"  Peak CPU: {usage.peak_cpu_percent:.1f}%")
                print(f"  State: {usage.state.value}")
                print(f"  Violations: {usage.cpu_violations}")

                if usage.state == TaskState.THROTTLED:
                    print("  ⚡ Task is being throttled!")

    finally:
        monitor.stop_monitoring()
        monitor.unregister_task("cpu_task")

        print(f"\n📊 Final Statistics:")
        print(f"  Peak CPU: {usage.peak_cpu_percent:.1f}%")
        print(f"  Average CPU: {usage.avg_cpu_percent:.1f}%")
        print(f"  CPU Violations: {usage.cpu_violations}")
        print(f"  Task Duration: {usage.duration:.2f}s")
        print(f"  Iterations: {iteration}")


def duration_limited_task(max_seconds: float = 5):
    """Simulate a task with duration limit"""
    print(f"\n{'='*60}")
    print(f"Starting duration-limited task (limit: {max_seconds}s)")
    print(f"{'='*60}")

    monitor = ResourceMonitor(check_interval=0.5)
    limits = ResourceLimits(
        max_duration_seconds=max_seconds,
        duration_limit_action=ResourceLimitAction.TERMINATE,
    )

    # Register task
    usage = monitor.register_task("duration_task", limits=limits)
    monitor.start_monitoring()

    try:
        while True:
            elapsed = usage.duration
            print(f"Running for {elapsed:.1f}s / {max_seconds}s")

            if usage.state == TaskState.TERMINATED:
                print("\n⏱️  Task terminated due to duration limit!")
                break

            time.sleep(1)

    finally:
        monitor.stop_monitoring()
        monitor.unregister_task("duration_task")

        print(f"\n📊 Final Statistics:")
        print(f"  Task Duration: {usage.duration:.2f}s")
        print(f"  Duration Violations: {usage.duration_violations}")


async def async_multi_task_demo():
    """Demonstrate monitoring multiple async tasks"""
    print(f"\n{'='*60}")
    print("Starting multi-task async monitoring demo")
    print(f"{'='*60}")

    monitor = ResourceMonitor()
    monitor.start_monitoring()

    async def worker(task_id: str, work_duration: float, memory_mb: int):
        """Async worker task"""
        limits = ResourceLimits(
            max_memory_mb=memory_mb, max_duration_seconds=work_duration * 2
        )

        usage = monitor.register_task(task_id, limits=limits)
        print(f"\n🚀 {task_id} started (memory limit: {memory_mb}MB)")

        # Simulate work
        data = bytearray(memory_mb // 2 * 1024 * 1024)  # Use half the limit
        await asyncio.sleep(work_duration)

        monitor.unregister_task(task_id)
        print(f"✅ {task_id} completed:")
        print(f"   Memory: {usage.peak_memory_mb:.1f}MB")
        print(f"   Duration: {usage.duration:.2f}s")

    # Start multiple tasks
    tasks = [
        worker("task_1", 2.0, 256),
        worker("task_2", 3.0, 512),
        worker("task_3", 1.5, 128),
        worker("task_4", 2.5, 384),
    ]

    await asyncio.gather(*tasks)

    # Show final statistics
    stats = monitor.get_statistics()
    print(f"\n📊 Overall Statistics:")
    print(f"  Total Tasks: {stats['total_tasks']}")
    print(f"  Total Suspensions: {stats['total_suspensions']}")
    print(f"  Total Throttles: {stats['total_throttles']}")
    print(f"  Total Terminations: {stats['total_terminations']}")

    monitor.stop_monitoring()


def suspension_and_resume_demo():
    """Demonstrate task suspension and resumption"""
    print(f"\n{'='*60}")
    print("Starting suspension and resume demo")
    print(f"{'='*60}")

    monitor = ResourceMonitor(check_interval=0.5)
    limits = ResourceLimits(
        max_memory_mb=100,  # Very low limit
        memory_limit_action=ResourceLimitAction.SUSPEND,
        memory_grace_period=1.0,
    )

    # Set up suspension callback
    def on_suspension(task_id, usage):
        print(f"\n🛑 Task {task_id} suspended!")
        print(f"   Memory at suspension: {usage.current_memory_mb:.1f}MB")

    monitor.set_suspension_callback(on_suspension)

    # Register task
    usage = monitor.register_task("suspend_task", limits=limits)
    monitor.start_monitoring()

    # Allocate memory to trigger suspension
    data = []
    try:
        for i in range(10):
            chunk = bytearray(30 * 1024 * 1024)  # 30MB chunks
            data.append(chunk)
            print(f"Allocated {(i+1)*30}MB - State: {usage.state.value}")

            if usage.state == TaskState.SUSPENDED:
                print("\n⏸️  Task is suspended. Waiting 3 seconds...")
                time.sleep(3)

                # Clear some memory
                data = data[:2]  # Keep only first 60MB

                # Resume task
                print("▶️  Resuming task...")
                monitor.resume_task("suspend_task")

            time.sleep(0.5)

    finally:
        monitor.stop_monitoring()
        monitor.unregister_task("suspend_task")

        print(f"\n📊 Final Statistics:")
        print(f"  Peak Memory: {usage.peak_memory_mb:.1f}MB")
        print(f"  Memory Violations: {usage.memory_violations}")
        print(f"  Final State: {usage.state.value}")


def main():
    """Run all demonstrations"""
    print("\n" + "=" * 70)
    print(" " * 20 + "RESOURCE MONITOR DEMONSTRATION")
    print("=" * 70)

    demos = [
        ("Memory Intensive Task", lambda: memory_intensive_task(200)),
        ("CPU Intensive Task", lambda: cpu_intensive_task(100)),
        ("Duration Limited Task", lambda: duration_limited_task(3)),
        ("Suspension and Resume", suspension_and_resume_demo),
        ("Async Multi-Task", lambda: asyncio.run(async_multi_task_demo())),
    ]

    for i, (name, demo_func) in enumerate(demos, 1):
        print(f"\n[{i}/{len(demos)}] Running: {name}")
        try:
            demo_func()
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            logger.exception("Demo error")

        if i < len(demos):
            print("\n" + "-" * 60)
            input("Press Enter to continue to next demo...")

    print("\n" + "=" * 70)
    print(" " * 25 + "DEMONSTRATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
