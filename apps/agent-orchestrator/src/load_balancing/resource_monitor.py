"""
System Resource Monitor
Real-time monitoring of system resources for intelligent load balancing decisions
"""
import asyncio
import logging
import platform
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import psutil

logger = logging.getLogger(__name__)


@dataclass
class SystemResources:
    """Current system resource state"""

    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    network_io_mbps: float
    active_processes: int
    load_average: List[float] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    @property
    def is_high_load(self) -> bool:
        """Check if system is under high load"""
        return (
            self.cpu_percent > 80
            or self.memory_percent > 85
            or (self.load_average and self.load_average[0] > psutil.cpu_count())
        )

    @property
    def is_moderate_load(self) -> bool:
        """Check if system is under moderate load"""
        return (
            self.cpu_percent > 60
            or self.memory_percent > 70
            or (self.load_average and self.load_average[0] > psutil.cpu_count() * 0.7)
        )

    @property
    def available_capacity(self) -> float:
        """Calculate available system capacity (0-1)"""
        cpu_capacity = max(0, (100 - self.cpu_percent) / 100)
        memory_capacity = max(0, (100 - self.memory_percent) / 100)
        return min(cpu_capacity, memory_capacity)


class ResourceMonitor:
    """System resource monitor with configurable collection intervals"""

    def __init__(self, collection_interval: float = 1.0, history_size: int = 300):
        self.collection_interval = collection_interval
        self.history_size = history_size

        # Resource history
        self._lock = threading.RLock()
        self._resource_history = deque(maxlen=history_size)
        self._current_resources: Optional[SystemResources] = None

        # Monitoring state
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None

        # Subscribers for resource updates
        self._subscribers: List[Callable[[SystemResources], None]] = []

        # Network monitoring state
        self._last_network_stats = None
        self._last_network_time = None

        logger.info(
            "ResourceMonitor initialized with %ds interval, %d history size",
            collection_interval,
            history_size,
        )

    def start_monitoring(self) -> None:
        """Start continuous resource monitoring"""
        if self._monitoring:
            logger.warning("Resource monitoring already running")
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self._monitor_thread.start()

        logger.info("Resource monitoring started")

    def stop_monitoring(self) -> None:
        """Stop resource monitoring"""
        if not self._monitoring:
            return

        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)

        logger.info("Resource monitoring stopped")

    def subscribe(self, callback: Callable[[SystemResources], None]) -> None:
        """Subscribe to resource updates"""
        with self._lock:
            self._subscribers.append(callback)
        logger.debug("Added resource monitor subscriber")

    def unsubscribe(self, callback: Callable[[SystemResources], None]) -> None:
        """Unsubscribe from resource updates"""
        with self._lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)
        logger.debug("Removed resource monitor subscriber")

    def get_current_resources(self) -> Optional[SystemResources]:
        """Get current resource state"""
        with self._lock:
            return self._current_resources

    def get_resource_history(self, seconds: int = 60) -> List[SystemResources]:
        """Get resource history for the last N seconds"""
        cutoff_time = time.time() - seconds
        with self._lock:
            return [
                res for res in self._resource_history if res.timestamp >= cutoff_time
            ]

    def get_average_resources(self, seconds: int = 60) -> Optional[SystemResources]:
        """Get average resource usage over the last N seconds"""
        history = self.get_resource_history(seconds)
        if not history:
            return None

        avg_cpu = sum(res.cpu_percent for res in history) / len(history)
        avg_memory = sum(res.memory_percent for res in history) / len(history)
        avg_memory_available = sum(res.memory_available_mb for res in history) / len(
            history
        )
        avg_disk = sum(res.disk_usage_percent for res in history) / len(history)
        avg_network = sum(res.network_io_mbps for res in history) / len(history)
        avg_processes = sum(res.active_processes for res in history) / len(history)

        return SystemResources(
            cpu_percent=round(avg_cpu, 2),
            memory_percent=round(avg_memory, 2),
            memory_available_mb=round(avg_memory_available, 2),
            disk_usage_percent=round(avg_disk, 2),
            network_io_mbps=round(avg_network, 2),
            active_processes=int(avg_processes),
            timestamp=time.time(),
        )

    def collect_resources(self) -> SystemResources:
        """Collect current system resources (synchronous)"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_mb = memory.available / (1024 * 1024)

            # Disk usage (root partition)
            try:
                disk = psutil.disk_usage("/")
                disk_usage_percent = disk.percent
            except Exception:
                disk_usage_percent = 0.0

            # Network I/O
            network_mbps = self._calculate_network_io()

            # Process count
            active_processes = len(psutil.pids())

            # Load average (Unix-like systems)
            load_avg = []
            if hasattr(psutil, "getloadavg"):
                try:
                    load_avg = list(psutil.getloadavg())
                except Exception:
                    pass

            return SystemResources(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                network_io_mbps=network_mbps,
                active_processes=active_processes,
                load_average=load_avg,
                timestamp=time.time(),
            )

        except Exception as e:
            logger.error("Error collecting system resources: %s", e)
            # Return safe defaults
            return SystemResources(
                cpu_percent=50.0,
                memory_percent=50.0,
                memory_available_mb=1024.0,
                disk_usage_percent=50.0,
                network_io_mbps=0.0,
                active_processes=100,
                timestamp=time.time(),
            )

    def _calculate_network_io(self) -> float:
        """Calculate network I/O in Mbps"""
        try:
            current_time = time.time()
            net_io = psutil.net_io_counters()
            current_stats = net_io.bytes_sent + net_io.bytes_recv

            if (
                self._last_network_stats is not None
                and self._last_network_time is not None
            ):
                bytes_diff = current_stats - self._last_network_stats
                time_diff = current_time - self._last_network_time

                if time_diff > 0:
                    mbps = (bytes_diff * 8) / (
                        1024 * 1024 * time_diff
                    )  # Convert to Mbps

                    # Update for next calculation
                    self._last_network_stats = current_stats
                    self._last_network_time = current_time

                    return max(0, mbps)

            # Initialize or reset
            self._last_network_stats = current_stats
            self._last_network_time = current_time
            return 0.0

        except Exception as e:
            logger.debug("Error calculating network I/O: %s", e)
            return 0.0

    def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        logger.debug("Resource monitoring loop started")

        while self._monitoring:
            try:
                # Collect resources
                resources = self.collect_resources()

                # Update current state and history
                with self._lock:
                    self._current_resources = resources
                    self._resource_history.append(resources)

                    # Notify subscribers
                    subscribers = list(self._subscribers)

                # Notify subscribers outside the lock
                for callback in subscribers:
                    try:
                        callback(resources)
                    except Exception as e:
                        logger.error("Error notifying resource subscriber: %s", e)

                # Wait for next collection
                time.sleep(self.collection_interval)

            except Exception as e:
                logger.error("Error in resource monitoring loop: %s", e)
                time.sleep(self.collection_interval)

        logger.debug("Resource monitoring loop stopped")

    def get_system_info(self) -> Dict[str, any]:
        """Get static system information"""
        try:
            return {
                "platform": platform.platform(),
                "cpu_count": psutil.cpu_count(),
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "total_memory_gb": round(
                    psutil.virtual_memory().total / (1024**3), 2
                ),
                "total_disk_gb": round(psutil.disk_usage("/").total / (1024**3), 2),
                "python_version": platform.python_version(),
                "architecture": platform.architecture()[0],
            }
        except Exception as e:
            logger.error("Error getting system info: %s", e)
            return {}

    def predict_resource_trend(self, minutes: int = 5) -> Dict[str, float]:
        """Predict resource usage trend based on historical data"""
        history = self.get_resource_history(minutes * 60)
        if len(history) < 10:  # Need minimum data points
            return {"cpu_trend": 0.0, "memory_trend": 0.0, "confidence": 0.0}

        # Simple linear trend calculation
        timestamps = [res.timestamp for res in history]
        cpu_values = [res.cpu_percent for res in history]
        memory_values = [res.memory_percent for res in history]

        # Calculate trends (simplified linear regression slope)
        n = len(history)
        sum_t = sum(timestamps)
        sum_cpu = sum(cpu_values)
        sum_memory = sum(memory_values)
        sum_t2 = sum(t * t for t in timestamps)
        sum_t_cpu = sum(t * cpu for t, cpu in zip(timestamps, cpu_values))
        sum_t_memory = sum(t * mem for t, mem in zip(timestamps, memory_values))

        # CPU trend (% per minute)
        cpu_trend = (n * sum_t_cpu - sum_t * sum_cpu) / (n * sum_t2 - sum_t * sum_t)
        cpu_trend *= 60  # Convert to per minute

        # Memory trend (% per minute)
        memory_trend = (n * sum_t_memory - sum_t * sum_memory) / (
            n * sum_t2 - sum_t * sum_t
        )
        memory_trend *= 60  # Convert to per minute

        # Confidence based on data consistency
        cpu_variance = sum((cpu - sum_cpu / n) ** 2 for cpu in cpu_values) / n
        memory_variance = sum((mem - sum_memory / n) ** 2 for mem in memory_values) / n
        confidence = max(
            0.1, 1.0 - (cpu_variance + memory_variance) / 2000
        )  # Simplified

        return {
            "cpu_trend": round(cpu_trend, 3),
            "memory_trend": round(memory_trend, 3),
            "confidence": round(confidence, 3),
        }


# Global resource monitor instance
_global_monitor: Optional[ResourceMonitor] = None


def get_global_resource_monitor() -> ResourceMonitor:
    """Get or create global resource monitor"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = ResourceMonitor()
        _global_monitor.start_monitoring()
    return _global_monitor


def shutdown_global_resource_monitor() -> None:
    """Shutdown global resource monitor"""
    global _global_monitor
    if _global_monitor:
        _global_monitor.stop_monitoring()
        _global_monitor = None
