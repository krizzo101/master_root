"""
Resource monitoring system for autonomous agent operations.

Monitors CPU, memory, disk usage, API tokens, and other resources to ensure
operations stay within defined limits and prevent resource exhaustion.
"""

import psutil
import asyncio
import time
from typing import Dict, Optional, List, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
import json
import os


class ResourceType(Enum):
    """Types of resources that can be monitored."""

    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    TOKENS = "tokens"
    API_CALLS = "api_calls"
    EXECUTION_TIME = "execution_time"
    NETWORK = "network"
    FILE_HANDLES = "file_handles"


@dataclass
class ResourceLimits:
    """Configurable resource limits for autonomous operations."""

    # CPU limits
    max_cpu_percent: float = 80.0  # Maximum CPU usage percentage
    cpu_check_interval: int = 5  # Seconds between CPU checks

    # Memory limits
    max_memory_mb: int = 4096  # Maximum memory usage in MB
    max_memory_percent: float = 75.0  # Maximum memory usage percentage

    # Disk limits
    max_disk_usage_gb: float = 10.0  # Maximum disk space for agent operations
    min_free_disk_gb: float = 5.0  # Minimum free disk space required

    # Token limits
    max_tokens_per_minute: int = 100000  # API token rate limit
    max_tokens_per_operation: int = 50000  # Single operation token limit
    max_total_tokens: int = 10000000  # Total token budget

    # API limits
    max_api_calls_per_minute: int = 60
    max_api_calls_per_hour: int = 1000

    # Time limits
    max_operation_seconds: int = 300  # Maximum time for single operation
    max_total_runtime_hours: float = 24.0  # Maximum total runtime

    # Network limits
    max_bandwidth_mbps: float = 100.0  # Maximum network bandwidth
    max_connections: int = 100  # Maximum concurrent connections

    # File system limits
    max_open_files: int = 1000
    max_file_size_mb: float = 100.0


@dataclass
class ResourceMetrics:
    """Current resource usage metrics."""

    timestamp: datetime = field(default_factory=datetime.now)
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    disk_used_gb: float = 0.0
    disk_free_gb: float = 0.0
    tokens_used: int = 0
    tokens_remaining: int = 0
    api_calls: int = 0
    execution_time_seconds: float = 0.0
    network_mbps: float = 0.0
    open_files: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "memory_percent": self.memory_percent,
            "disk_used_gb": self.disk_used_gb,
            "disk_free_gb": self.disk_free_gb,
            "tokens_used": self.tokens_used,
            "tokens_remaining": self.tokens_remaining,
            "api_calls": self.api_calls,
            "execution_time_seconds": self.execution_time_seconds,
            "network_mbps": self.network_mbps,
            "open_files": self.open_files,
        }


class ResourceMonitor:
    """
    Comprehensive resource monitoring system with real-time tracking
    and automatic throttling capabilities.
    """

    def __init__(
        self,
        limits: Optional[ResourceLimits] = None,
        audit_logger: Optional[Any] = None,
        enable_auto_throttle: bool = True,
    ):
        """
        Initialize resource monitor.

        Args:
            limits: Resource limits configuration
            audit_logger: Optional audit logger instance
            enable_auto_throttle: Whether to automatically throttle on limit breach
        """
        self.limits = limits or ResourceLimits()
        self.audit_logger = audit_logger
        self.enable_auto_throttle = enable_auto_throttle

        # Tracking variables
        self.start_time = datetime.now()
        self.total_tokens = 0
        self.total_api_calls = 0
        self.token_window: List[tuple] = []  # (timestamp, count) pairs
        self.api_window: List[tuple] = []

        # Monitoring state
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._callbacks: Dict[ResourceType, List[Callable]] = {}
        self._throttle_state: Dict[ResourceType, bool] = {}

        # Metrics history
        self.metrics_history: List[ResourceMetrics] = []
        self.max_history_size = 1000

    def start_monitoring(self) -> None:
        """Start background resource monitoring."""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

        if self.audit_logger:
            self.audit_logger.log_event(
                event_type="RESOURCE_MONITORING_STARTED", details={"limits": self.limits.__dict__}
            )

    def stop_monitoring(self) -> None:
        """Stop background resource monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

        if self.audit_logger:
            self.audit_logger.log_event(
                event_type="RESOURCE_MONITORING_STOPPED",
                details={"total_runtime": self.get_runtime_seconds()},
            )

    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while self._monitoring:
            try:
                metrics = self.get_current_metrics()
                self._check_limits(metrics)
                self._record_metrics(metrics)
                time.sleep(self.limits.cpu_check_interval)
            except Exception as e:
                if self.audit_logger:
                    self.audit_logger.log_error("Resource monitoring error", {"error": str(e)})

    def get_current_metrics(self) -> ResourceMetrics:
        """Get current resource usage metrics."""
        metrics = ResourceMetrics()

        # CPU metrics
        metrics.cpu_percent = psutil.cpu_percent(interval=1)

        # Memory metrics
        memory = psutil.virtual_memory()
        metrics.memory_mb = memory.used / (1024 * 1024)
        metrics.memory_percent = memory.percent

        # Disk metrics
        disk = psutil.disk_usage("/")
        metrics.disk_used_gb = disk.used / (1024 * 1024 * 1024)
        metrics.disk_free_gb = disk.free / (1024 * 1024 * 1024)

        # Token and API metrics
        metrics.tokens_used = self.total_tokens
        metrics.tokens_remaining = self.limits.max_total_tokens - self.total_tokens
        metrics.api_calls = self.total_api_calls

        # Execution time
        metrics.execution_time_seconds = self.get_runtime_seconds()

        # Network metrics (simplified)
        try:
            net_io = psutil.net_io_counters()
            # Simple bandwidth estimation
            metrics.network_mbps = (net_io.bytes_sent + net_io.bytes_recv) / (1024 * 1024)
        except:
            metrics.network_mbps = 0.0

        # File handles
        try:
            process = psutil.Process()
            metrics.open_files = len(process.open_files())
        except:
            metrics.open_files = 0

        return metrics

    def _check_limits(self, metrics: ResourceMetrics) -> None:
        """Check if any resource limits are breached."""
        violations = []

        # Check CPU limit
        if metrics.cpu_percent > self.limits.max_cpu_percent:
            violations.append((ResourceType.CPU, metrics.cpu_percent))

        # Check memory limits
        if metrics.memory_mb > self.limits.max_memory_mb:
            violations.append((ResourceType.MEMORY, metrics.memory_mb))

        if metrics.memory_percent > self.limits.max_memory_percent:
            violations.append((ResourceType.MEMORY, metrics.memory_percent))

        # Check disk limits
        if metrics.disk_free_gb < self.limits.min_free_disk_gb:
            violations.append((ResourceType.DISK, metrics.disk_free_gb))

        # Check token limits
        if metrics.tokens_used > self.limits.max_total_tokens:
            violations.append((ResourceType.TOKENS, metrics.tokens_used))

        # Check execution time
        max_seconds = self.limits.max_total_runtime_hours * 3600
        if metrics.execution_time_seconds > max_seconds:
            violations.append((ResourceType.EXECUTION_TIME, metrics.execution_time_seconds))

        # Handle violations
        for resource_type, value in violations:
            self._handle_violation(resource_type, value, metrics)

    def _handle_violation(
        self, resource_type: ResourceType, value: float, metrics: ResourceMetrics
    ) -> None:
        """Handle resource limit violation."""
        if self.audit_logger:
            self.audit_logger.log_warning(
                f"Resource limit violation: {resource_type.value}",
                {"value": value, "metrics": metrics.to_dict()},
            )

        # Trigger callbacks
        if resource_type in self._callbacks:
            for callback in self._callbacks[resource_type]:
                try:
                    callback(resource_type, value, metrics)
                except Exception as e:
                    if self.audit_logger:
                        self.audit_logger.log_error("Callback execution failed", {"error": str(e)})

        # Auto-throttle if enabled
        if self.enable_auto_throttle:
            self._apply_throttle(resource_type)

    def _apply_throttle(self, resource_type: ResourceType) -> None:
        """Apply automatic throttling for resource type."""
        self._throttle_state[resource_type] = True

        if resource_type == ResourceType.CPU:
            # Reduce CPU usage by adding sleep
            time.sleep(0.5)
        elif resource_type == ResourceType.MEMORY:
            # Trigger garbage collection
            import gc

            gc.collect()
        elif resource_type == ResourceType.TOKENS:
            # Pause token consumption
            time.sleep(60)  # Wait 1 minute

    def _record_metrics(self, metrics: ResourceMetrics) -> None:
        """Record metrics to history."""
        self.metrics_history.append(metrics)

        # Trim history if too large
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size :]

    def register_callback(self, resource_type: ResourceType, callback: Callable) -> None:
        """Register callback for resource limit violations."""
        if resource_type not in self._callbacks:
            self._callbacks[resource_type] = []
        self._callbacks[resource_type].append(callback)

    def track_tokens(self, count: int) -> bool:
        """
        Track token usage and check limits.

        Args:
            count: Number of tokens to add

        Returns:
            True if within limits, False if limit exceeded
        """
        now = datetime.now()

        # Update total
        self.total_tokens += count

        # Update window for rate limiting
        self.token_window.append((now, count))

        # Clean old entries (older than 1 minute)
        cutoff = now - timedelta(minutes=1)
        self.token_window = [(ts, c) for ts, c in self.token_window if ts > cutoff]

        # Check rate limit
        window_total = sum(c for _, c in self.token_window)
        if window_total > self.limits.max_tokens_per_minute:
            if self.audit_logger:
                self.audit_logger.log_warning(
                    "Token rate limit exceeded",
                    {"window_total": window_total, "limit": self.limits.max_tokens_per_minute},
                )
            return False

        # Check operation limit
        if count > self.limits.max_tokens_per_operation:
            return False

        # Check total limit
        if self.total_tokens > self.limits.max_total_tokens:
            return False

        return True

    def track_api_call(self) -> bool:
        """
        Track API call and check limits.

        Returns:
            True if within limits, False if limit exceeded
        """
        now = datetime.now()
        self.total_api_calls += 1

        # Update window
        self.api_window.append((now, 1))

        # Clean old entries
        minute_cutoff = now - timedelta(minutes=1)
        hour_cutoff = now - timedelta(hours=1)

        # Check per-minute limit
        minute_window = [(ts, c) for ts, c in self.api_window if ts > minute_cutoff]
        if len(minute_window) > self.limits.max_api_calls_per_minute:
            return False

        # Check per-hour limit
        hour_window = [(ts, c) for ts, c in self.api_window if ts > hour_cutoff]
        if len(hour_window) > self.limits.max_api_calls_per_hour:
            return False

        # Update window
        self.api_window = hour_window

        return True

    def get_runtime_seconds(self) -> float:
        """Get total runtime in seconds."""
        return (datetime.now() - self.start_time).total_seconds()

    def get_resource_usage_summary(self) -> Dict[str, Any]:
        """Get comprehensive resource usage summary."""
        metrics = self.get_current_metrics()

        return {
            "current_metrics": metrics.to_dict(),
            "total_runtime_hours": self.get_runtime_seconds() / 3600,
            "total_tokens": self.total_tokens,
            "total_api_calls": self.total_api_calls,
            "throttle_states": {k.value: v for k, v in self._throttle_state.items()},
            "limits": {
                "cpu_percent": self.limits.max_cpu_percent,
                "memory_mb": self.limits.max_memory_mb,
                "tokens": self.limits.max_total_tokens,
                "runtime_hours": self.limits.max_total_runtime_hours,
            },
        }

    def export_metrics_history(self, filepath: str) -> None:
        """Export metrics history to JSON file."""
        data = [m.to_dict() for m in self.metrics_history]
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def is_within_limits(self) -> bool:
        """Check if all resources are within limits."""
        metrics = self.get_current_metrics()

        checks = [
            metrics.cpu_percent <= self.limits.max_cpu_percent,
            metrics.memory_mb <= self.limits.max_memory_mb,
            metrics.memory_percent <= self.limits.max_memory_percent,
            metrics.disk_free_gb >= self.limits.min_free_disk_gb,
            metrics.tokens_used <= self.limits.max_total_tokens,
            metrics.execution_time_seconds <= self.limits.max_total_runtime_hours * 3600,
        ]

        return all(checks)

    async def check_before_operation(
        self, estimated_tokens: int = 0, estimated_time_seconds: float = 0
    ) -> bool:
        """
        Pre-flight check before starting an operation.

        Args:
            estimated_tokens: Estimated tokens for operation
            estimated_time_seconds: Estimated time for operation

        Returns:
            True if operation can proceed, False otherwise
        """
        if not self.is_within_limits():
            return False

        # Check if operation would exceed limits
        if estimated_tokens > 0:
            if self.total_tokens + estimated_tokens > self.limits.max_total_tokens:
                return False
            if estimated_tokens > self.limits.max_tokens_per_operation:
                return False

        if estimated_time_seconds > 0:
            if estimated_time_seconds > self.limits.max_operation_seconds:
                return False

        return True
