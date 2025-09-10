"""
Enhanced Resource Monitor with Task-Level Limits and Throttling
Provides per-task resource limits, CPU throttling, and automatic task suspension
"""

import asyncio
import logging
import os
import resource
import signal
import threading
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import psutil

logger = logging.getLogger(__name__)


class ResourceLimitAction(Enum):
    """Actions to take when resource limits are exceeded"""

    WARN = "warn"
    THROTTLE = "throttle"
    SUSPEND = "suspend"
    TERMINATE = "terminate"


class TaskState(Enum):
    """Task execution states"""

    RUNNING = "running"
    THROTTLED = "throttled"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    COMPLETED = "completed"


@dataclass
class ResourceLimits:
    """Resource limits configuration for a task"""

    max_memory_mb: Optional[float] = None  # Maximum memory in MB
    max_cpu_percent: Optional[float] = None  # Maximum CPU percentage (0-100 per core)
    max_duration_seconds: Optional[float] = None  # Maximum execution time
    max_file_handles: Optional[int] = None  # Maximum open file descriptors
    max_threads: Optional[int] = None  # Maximum thread count

    # Actions when limits exceeded
    memory_limit_action: ResourceLimitAction = ResourceLimitAction.SUSPEND
    cpu_limit_action: ResourceLimitAction = ResourceLimitAction.THROTTLE
    duration_limit_action: ResourceLimitAction = ResourceLimitAction.TERMINATE

    # Throttling parameters
    cpu_throttle_factor: float = 0.5  # Reduce CPU to this factor when throttling
    throttle_check_interval: float = 0.1  # Check interval in seconds

    # Grace periods before taking action
    memory_grace_period: float = 5.0  # Seconds before suspending
    cpu_grace_period: float = 10.0  # Seconds before throttling

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "max_memory_mb": self.max_memory_mb,
            "max_cpu_percent": self.max_cpu_percent,
            "max_duration_seconds": self.max_duration_seconds,
            "max_file_handles": self.max_file_handles,
            "max_threads": self.max_threads,
            "memory_limit_action": self.memory_limit_action.value,
            "cpu_limit_action": self.cpu_limit_action.value,
            "duration_limit_action": self.duration_limit_action.value,
            "cpu_throttle_factor": self.cpu_throttle_factor,
            "throttle_check_interval": self.throttle_check_interval,
            "memory_grace_period": self.memory_grace_period,
            "cpu_grace_period": self.cpu_grace_period,
        }


@dataclass
class TaskResourceUsage:
    """Resource usage tracking for a task"""

    task_id: str
    process_id: Optional[int] = None
    start_time: datetime = field(default_factory=datetime.now)

    # Current usage
    current_memory_mb: float = 0.0
    current_cpu_percent: float = 0.0
    current_threads: int = 0
    current_file_handles: int = 0

    # Peak usage
    peak_memory_mb: float = 0.0
    peak_cpu_percent: float = 0.0
    peak_threads: int = 0

    # Historical data
    memory_history: deque = field(default_factory=lambda: deque(maxlen=100))
    cpu_history: deque = field(default_factory=lambda: deque(maxlen=100))

    # Violation tracking
    memory_violations: int = 0
    cpu_violations: int = 0
    duration_violations: int = 0

    # State
    state: TaskState = TaskState.RUNNING
    suspended_at: Optional[datetime] = None
    throttled_at: Optional[datetime] = None

    @property
    def duration(self) -> float:
        """Get task duration in seconds"""
        return (datetime.now() - self.start_time).total_seconds()

    @property
    def avg_memory_mb(self) -> float:
        """Average memory usage"""
        return (
            sum(self.memory_history) / len(self.memory_history)
            if self.memory_history
            else 0
        )

    @property
    def avg_cpu_percent(self) -> float:
        """Average CPU usage"""
        return sum(self.cpu_history) / len(self.cpu_history) if self.cpu_history else 0

    def update(
        self,
        memory_mb: float,
        cpu_percent: float,
        threads: int = 0,
        file_handles: int = 0,
    ):
        """Update current usage metrics"""
        self.current_memory_mb = memory_mb
        self.current_cpu_percent = cpu_percent
        self.current_threads = threads
        self.current_file_handles = file_handles

        # Update peaks
        self.peak_memory_mb = max(self.peak_memory_mb, memory_mb)
        self.peak_cpu_percent = max(self.peak_cpu_percent, cpu_percent)
        self.peak_threads = max(self.peak_threads, threads)

        # Update history
        self.memory_history.append(memory_mb)
        self.cpu_history.append(cpu_percent)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "task_id": self.task_id,
            "process_id": self.process_id,
            "start_time": self.start_time.isoformat(),
            "duration": self.duration,
            "state": self.state.value,
            "current": {
                "memory_mb": round(self.current_memory_mb, 2),
                "cpu_percent": round(self.current_cpu_percent, 2),
                "threads": self.current_threads,
                "file_handles": self.current_file_handles,
            },
            "peak": {
                "memory_mb": round(self.peak_memory_mb, 2),
                "cpu_percent": round(self.peak_cpu_percent, 2),
                "threads": self.peak_threads,
            },
            "average": {
                "memory_mb": round(self.avg_memory_mb, 2),
                "cpu_percent": round(self.avg_cpu_percent, 2),
            },
            "violations": {
                "memory": self.memory_violations,
                "cpu": self.cpu_violations,
                "duration": self.duration_violations,
            },
        }


class ResourceMonitor:
    """
    Enhanced resource monitor with per-task limits and throttling capabilities.
    Integrates with the monitoring module to provide comprehensive resource management.
    """

    def __init__(
        self,
        default_limits: Optional[ResourceLimits] = None,
        check_interval: float = 1.0,
        enable_system_limits: bool = True,
    ):
        """
        Initialize resource monitor

        Args:
            default_limits: Default limits for tasks without specific limits
            check_interval: Interval for checking resource usage
            enable_system_limits: Enable OS-level resource limits
        """
        self.default_limits = default_limits or ResourceLimits(
            max_memory_mb=2048,  # 2GB default
            max_cpu_percent=200,  # 200% (2 cores) default
            max_duration_seconds=3600,  # 1 hour default
            max_threads=50,
        )
        self.check_interval = check_interval
        self.enable_system_limits = enable_system_limits

        # Task tracking
        self._tasks: Dict[str, TaskResourceUsage] = {}
        self._task_limits: Dict[str, ResourceLimits] = {}
        self._task_processes: Dict[str, psutil.Process] = {}

        # Monitoring state
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

        # Callbacks
        self._violation_callbacks: List[Callable] = []
        self._suspension_callbacks: List[Callable] = []

        # Statistics
        self._total_suspensions = 0
        self._total_throttles = 0
        self._total_terminations = 0

        logger.info(
            "ResourceMonitor initialized with check interval: %.1fs", check_interval
        )

    def start_monitoring(self):
        """Start the resource monitoring thread"""
        with self._lock:
            if self._monitoring:
                logger.warning("Resource monitoring already running")
                return

            self._monitoring = True
            self._monitor_thread = threading.Thread(
                target=self._monitoring_loop, daemon=True
            )
            self._monitor_thread.start()
            logger.info("Resource monitoring started")

    def stop_monitoring(self):
        """Stop the resource monitoring thread"""
        with self._lock:
            if not self._monitoring:
                return

            self._monitoring = False

        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)

        logger.info("Resource monitoring stopped")

    def register_task(
        self,
        task_id: str,
        process_id: Optional[int] = None,
        limits: Optional[ResourceLimits] = None,
    ) -> TaskResourceUsage:
        """
        Register a task for monitoring

        Args:
            task_id: Unique task identifier
            process_id: Process ID to monitor (None for current process)
            limits: Resource limits for this task

        Returns:
            TaskResourceUsage object for tracking
        """
        with self._lock:
            if task_id in self._tasks:
                logger.warning("Task %s already registered", task_id)
                return self._tasks[task_id]

            # Use provided limits or defaults
            task_limits = limits or self.default_limits
            self._task_limits[task_id] = task_limits

            # Create usage tracker
            usage = TaskResourceUsage(
                task_id=task_id, process_id=process_id or os.getpid()
            )
            self._tasks[task_id] = usage

            # Get process handle
            try:
                process = psutil.Process(usage.process_id)
                self._task_processes[task_id] = process

                # Apply OS-level limits if enabled
                if self.enable_system_limits:
                    self._apply_os_limits(process, task_limits)

            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.error("Failed to get process for task %s: %s", task_id, e)

            logger.info("Registered task %s with PID %d", task_id, usage.process_id)
            return usage

    def unregister_task(self, task_id: str):
        """Unregister a task from monitoring"""
        with self._lock:
            if task_id not in self._tasks:
                return

            usage = self._tasks[task_id]
            usage.state = TaskState.COMPLETED

            # Clean up
            self._task_processes.pop(task_id, None)
            self._task_limits.pop(task_id, None)

            logger.info("Unregistered task %s", task_id)

    def suspend_task(self, task_id: str) -> bool:
        """
        Suspend a task

        Args:
            task_id: Task to suspend

        Returns:
            True if suspended successfully
        """
        with self._lock:
            if task_id not in self._tasks:
                logger.warning("Task %s not found", task_id)
                return False

            usage = self._tasks[task_id]
            process = self._task_processes.get(task_id)

            if not process:
                logger.warning("No process found for task %s", task_id)
                return False

            try:
                # Suspend the process
                process.suspend()
                usage.state = TaskState.SUSPENDED
                usage.suspended_at = datetime.now()
                self._total_suspensions += 1

                logger.info("Suspended task %s (PID %d)", task_id, process.pid)

                # Notify callbacks
                for callback in self._suspension_callbacks:
                    try:
                        callback(task_id, usage)
                    except Exception as e:
                        logger.error("Error in suspension callback: %s", e)

                return True

            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.error("Failed to suspend task %s: %s", task_id, e)
                return False

    def resume_task(self, task_id: str) -> bool:
        """
        Resume a suspended task

        Args:
            task_id: Task to resume

        Returns:
            True if resumed successfully
        """
        with self._lock:
            if task_id not in self._tasks:
                logger.warning("Task %s not found", task_id)
                return False

            usage = self._tasks[task_id]
            process = self._task_processes.get(task_id)

            if not process:
                logger.warning("No process found for task %s", task_id)
                return False

            if usage.state != TaskState.SUSPENDED:
                logger.warning("Task %s is not suspended", task_id)
                return False

            try:
                # Resume the process
                process.resume()
                usage.state = TaskState.RUNNING
                usage.suspended_at = None

                logger.info("Resumed task %s (PID %d)", task_id, process.pid)
                return True

            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.error("Failed to resume task %s: %s", task_id, e)
                return False

    def throttle_task(
        self, task_id: str, cpu_affinity: Optional[List[int]] = None
    ) -> bool:
        """
        Throttle a task's CPU usage

        Args:
            task_id: Task to throttle
            cpu_affinity: CPU cores to restrict to (None for automatic)

        Returns:
            True if throttled successfully
        """
        with self._lock:
            if task_id not in self._tasks:
                logger.warning("Task %s not found", task_id)
                return False

            usage = self._tasks[task_id]
            process = self._task_processes.get(task_id)
            limits = self._task_limits[task_id]

            if not process:
                logger.warning("No process found for task %s", task_id)
                return False

            try:
                # Set CPU affinity to limit cores
                if cpu_affinity is None:
                    # Use half the available cores
                    available_cpus = list(range(psutil.cpu_count()))
                    cpu_affinity = available_cpus[: len(available_cpus) // 2] or [0]

                process.cpu_affinity(cpu_affinity)

                # Lower process priority
                if os.name == "posix":
                    process.nice(10)  # Lower priority on Unix
                else:
                    process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)  # Windows

                usage.state = TaskState.THROTTLED
                usage.throttled_at = datetime.now()
                self._total_throttles += 1

                logger.info("Throttled task %s to CPUs %s", task_id, cpu_affinity)
                return True

            except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError) as e:
                logger.error("Failed to throttle task %s: %s", task_id, e)
                return False

    def terminate_task(self, task_id: str, timeout: float = 5.0) -> bool:
        """
        Terminate a task

        Args:
            task_id: Task to terminate
            timeout: Timeout for graceful termination

        Returns:
            True if terminated successfully
        """
        with self._lock:
            if task_id not in self._tasks:
                logger.warning("Task %s not found", task_id)
                return False

            usage = self._tasks[task_id]
            process = self._task_processes.get(task_id)

            if not process:
                logger.warning("No process found for task %s", task_id)
                return False

            try:
                # Try graceful termination first
                process.terminate()
                process.wait(timeout=timeout)

            except psutil.TimeoutExpired:
                # Force kill if graceful termination fails
                try:
                    process.kill()
                    process.wait(timeout=2)
                except Exception as e:
                    logger.error("Failed to kill task %s: %s", task_id, e)
                    return False
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.error("Failed to terminate task %s: %s", task_id, e)
                return False

            usage.state = TaskState.TERMINATED
            self._total_terminations += 1

            logger.info("Terminated task %s", task_id)
            return True

    def get_task_usage(self, task_id: str) -> Optional[TaskResourceUsage]:
        """Get current resource usage for a task"""
        with self._lock:
            return self._tasks.get(task_id)

    def get_all_tasks(self) -> Dict[str, TaskResourceUsage]:
        """Get all monitored tasks"""
        with self._lock:
            return self._tasks.copy()

    def set_violation_callback(self, callback: Callable):
        """Add a callback for resource violations"""
        self._violation_callbacks.append(callback)

    def set_suspension_callback(self, callback: Callable):
        """Add a callback for task suspensions"""
        self._suspension_callbacks.append(callback)

    def get_statistics(self) -> Dict[str, Any]:
        """Get monitor statistics"""
        with self._lock:
            active_tasks = sum(
                1 for t in self._tasks.values() if t.state == TaskState.RUNNING
            )
            suspended_tasks = sum(
                1 for t in self._tasks.values() if t.state == TaskState.SUSPENDED
            )
            throttled_tasks = sum(
                1 for t in self._tasks.values() if t.state == TaskState.THROTTLED
            )

            return {
                "active_tasks": active_tasks,
                "suspended_tasks": suspended_tasks,
                "throttled_tasks": throttled_tasks,
                "total_tasks": len(self._tasks),
                "total_suspensions": self._total_suspensions,
                "total_throttles": self._total_throttles,
                "total_terminations": self._total_terminations,
                "monitoring": self._monitoring,
            }

    def _monitoring_loop(self):
        """Main monitoring loop"""
        logger.debug("Resource monitoring loop started")

        while self._monitoring:
            try:
                # Check all tasks
                with self._lock:
                    tasks_to_check = list(self._tasks.items())

                for task_id, usage in tasks_to_check:
                    if usage.state not in [TaskState.RUNNING, TaskState.THROTTLED]:
                        continue

                    self._check_task_resources(task_id, usage)

                # Wait for next check
                time.sleep(self.check_interval)

            except Exception as e:
                logger.error("Error in monitoring loop: %s", e)
                time.sleep(self.check_interval)

        logger.debug("Resource monitoring loop stopped")

    def _check_task_resources(self, task_id: str, usage: TaskResourceUsage):
        """Check resource usage for a task"""
        try:
            process = self._task_processes.get(task_id)
            if not process or not process.is_running():
                return

            limits = self._task_limits[task_id]

            # Get current usage
            with process.oneshot():
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)
                cpu_percent = process.cpu_percent(interval=0.1)

                try:
                    threads = process.num_threads()
                    file_handles = len(process.open_files())
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    threads = 0
                    file_handles = 0

            # Update usage
            usage.update(memory_mb, cpu_percent, threads, file_handles)

            # Check memory limit
            if limits.max_memory_mb and memory_mb > limits.max_memory_mb:
                self._handle_memory_violation(task_id, usage, memory_mb, limits)

            # Check CPU limit
            if limits.max_cpu_percent and cpu_percent > limits.max_cpu_percent:
                self._handle_cpu_violation(task_id, usage, cpu_percent, limits)

            # Check duration limit
            if (
                limits.max_duration_seconds
                and usage.duration > limits.max_duration_seconds
            ):
                self._handle_duration_violation(task_id, usage, limits)

            # Check thread limit
            if limits.max_threads and threads > limits.max_threads:
                logger.warning(
                    "Task %s exceeds thread limit: %d > %d",
                    task_id,
                    threads,
                    limits.max_threads,
                )

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.debug("Process no longer accessible for task %s: %s", task_id, e)
            usage.state = TaskState.COMPLETED
        except Exception as e:
            logger.error("Error checking resources for task %s: %s", task_id, e)

    def _handle_memory_violation(
        self,
        task_id: str,
        usage: TaskResourceUsage,
        memory_mb: float,
        limits: ResourceLimits,
    ):
        """Handle memory limit violation"""
        usage.memory_violations += 1

        logger.warning(
            "Task %s exceeds memory limit: %.1f MB > %.1f MB",
            task_id,
            memory_mb,
            limits.max_memory_mb,
        )

        # Notify callbacks
        for callback in self._violation_callbacks:
            try:
                callback(task_id, "memory", memory_mb, limits.max_memory_mb)
            except Exception as e:
                logger.error("Error in violation callback: %s", e)

        # Take action based on configuration
        if limits.memory_limit_action == ResourceLimitAction.SUSPEND:
            # Check grace period
            if (
                usage.memory_violations * self.check_interval
                >= limits.memory_grace_period
            ):
                logger.warning(
                    "Suspending task %s due to memory limit violation", task_id
                )
                self.suspend_task(task_id)

        elif limits.memory_limit_action == ResourceLimitAction.TERMINATE:
            logger.warning("Terminating task %s due to memory limit violation", task_id)
            self.terminate_task(task_id)

    def _handle_cpu_violation(
        self,
        task_id: str,
        usage: TaskResourceUsage,
        cpu_percent: float,
        limits: ResourceLimits,
    ):
        """Handle CPU limit violation"""
        usage.cpu_violations += 1

        logger.warning(
            "Task %s exceeds CPU limit: %.1f%% > %.1f%%",
            task_id,
            cpu_percent,
            limits.max_cpu_percent,
        )

        # Notify callbacks
        for callback in self._violation_callbacks:
            try:
                callback(task_id, "cpu", cpu_percent, limits.max_cpu_percent)
            except Exception as e:
                logger.error("Error in violation callback: %s", e)

        # Take action based on configuration
        if limits.cpu_limit_action == ResourceLimitAction.THROTTLE:
            # Check grace period
            if usage.cpu_violations * self.check_interval >= limits.cpu_grace_period:
                if usage.state != TaskState.THROTTLED:
                    logger.warning(
                        "Throttling task %s due to CPU limit violation", task_id
                    )
                    self.throttle_task(task_id)

        elif limits.cpu_limit_action == ResourceLimitAction.SUSPEND:
            logger.warning("Suspending task %s due to CPU limit violation", task_id)
            self.suspend_task(task_id)

    def _handle_duration_violation(
        self, task_id: str, usage: TaskResourceUsage, limits: ResourceLimits
    ):
        """Handle duration limit violation"""
        usage.duration_violations += 1

        logger.warning(
            "Task %s exceeds duration limit: %.1fs > %.1fs",
            task_id,
            usage.duration,
            limits.max_duration_seconds,
        )

        # Notify callbacks
        for callback in self._violation_callbacks:
            try:
                callback(
                    task_id, "duration", usage.duration, limits.max_duration_seconds
                )
            except Exception as e:
                logger.error("Error in violation callback: %s", e)

        # Take action based on configuration
        if limits.duration_limit_action == ResourceLimitAction.TERMINATE:
            logger.warning("Terminating task %s due to duration limit", task_id)
            self.terminate_task(task_id)
        elif limits.duration_limit_action == ResourceLimitAction.SUSPEND:
            logger.warning("Suspending task %s due to duration limit", task_id)
            self.suspend_task(task_id)

    def _apply_os_limits(self, process: psutil.Process, limits: ResourceLimits):
        """Apply OS-level resource limits to a process"""
        if not hasattr(resource, "setrlimit"):
            return  # Not supported on this platform

        try:
            pid = process.pid

            # Set memory limit
            if limits.max_memory_mb:
                max_bytes = int(limits.max_memory_mb * 1024 * 1024)
                resource.prlimit(pid, resource.RLIMIT_AS, (max_bytes, max_bytes))

            # Set CPU time limit
            if limits.max_duration_seconds:
                cpu_seconds = int(limits.max_duration_seconds)
                resource.prlimit(pid, resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))

            # Set file descriptor limit
            if limits.max_file_handles:
                resource.prlimit(
                    pid,
                    resource.RLIMIT_NOFILE,
                    (limits.max_file_handles, limits.max_file_handles),
                )

            logger.debug("Applied OS limits to process %d", pid)

        except Exception as e:
            logger.warning("Failed to apply OS limits: %s", e)

    @contextmanager
    def monitor_task(self, task_id: str, limits: Optional[ResourceLimits] = None):
        """
        Context manager for monitoring a task

        Usage:
            with monitor.monitor_task("my_task", limits) as usage:
                # Task code here
                pass
        """
        usage = self.register_task(task_id, limits=limits)
        try:
            yield usage
        finally:
            self.unregister_task(task_id)
            logger.info("Task %s resource summary: %s", task_id, usage.to_dict())


# Global resource monitor instance
_global_monitor: Optional[ResourceMonitor] = None


def get_global_resource_monitor() -> ResourceMonitor:
    """Get or create global resource monitor"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = ResourceMonitor()
        _global_monitor.start_monitoring()
    return _global_monitor


def shutdown_global_resource_monitor():
    """Shutdown global resource monitor"""
    global _global_monitor
    if _global_monitor:
        _global_monitor.stop_monitoring()
        _global_monitor = None
