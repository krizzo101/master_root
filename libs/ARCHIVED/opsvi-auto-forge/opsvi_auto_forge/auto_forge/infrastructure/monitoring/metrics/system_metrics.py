"""System metrics for production monitoring."""

import asyncio
import time

import psutil
import structlog
from prometheus_client import Counter, Gauge, Histogram

logger = structlog.get_logger()

# System Health Metrics
SYSTEM_UP = Gauge("system_up", "System health status (1 = healthy, 0 = unhealthy)")
SYSTEM_START_TIME = Gauge(
    "system_start_time_seconds", "System start time in seconds since epoch"
)

# Resource Usage Metrics
CPU_USAGE_PERCENT = Gauge("cpu_usage_percent", "CPU usage percentage")
MEMORY_USAGE_BYTES = Gauge("memory_usage_bytes", "Memory usage in bytes")
MEMORY_USAGE_PERCENT = Gauge("memory_usage_percent", "Memory usage percentage")
DISK_USAGE_BYTES = Gauge("disk_usage_bytes", "Disk usage in bytes", ["mount_point"])
DISK_USAGE_PERCENT = Gauge(
    "disk_usage_percent", "Disk usage percentage", ["mount_point"]
)

# Network Metrics
NETWORK_BYTES_SENT = Counter(
    "network_bytes_sent_total", "Total bytes sent", ["interface"]
)
NETWORK_BYTES_RECEIVED = Counter(
    "network_bytes_received_total", "Total bytes received", ["interface"]
)
NETWORK_PACKETS_SENT = Counter(
    "network_packets_sent_total", "Total packets sent", ["interface"]
)
NETWORK_PACKETS_RECEIVED = Counter(
    "network_packets_received_total", "Total packets received", ["interface"]
)

# Application Performance Metrics
TASK_EXECUTION_DURATION = Histogram(
    "task_execution_duration_seconds",
    "Task execution duration in seconds",
    ["task_type", "status"],
)

TASK_QUEUE_SIZE = Gauge("task_queue_size", "Number of tasks in queue", ["queue_name"])
TASK_PROCESSING_RATE = Counter(
    "task_processing_total", "Total tasks processed", ["task_type", "status"]
)

# Database Metrics
DB_CONNECTION_POOL_SIZE = Gauge(
    "db_connection_pool_size", "Database connection pool size"
)
DB_CONNECTION_POOL_ACTIVE = Gauge(
    "db_connection_pool_active", "Active database connections"
)
DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds", "Database query duration", ["query_type"]
)
DB_QUERY_ERRORS = Counter(
    "db_query_errors_total", "Database query errors", ["query_type"]
)

# Cache Metrics
CACHE_HIT_RATIO = Gauge("cache_hit_ratio", "Cache hit ratio")
CACHE_SIZE = Gauge("cache_size", "Cache size in bytes")
CACHE_EVICTIONS = Counter("cache_evictions_total", "Cache evictions", ["cache_type"])

# Error and Exception Metrics
EXCEPTION_COUNT = Counter(
    "exceptions_total", "Total exceptions", ["exception_type", "module"]
)
ERROR_RATE = Gauge("error_rate", "Error rate per minute", ["error_type"])

# Business Logic Metrics
TASK_SUCCESS_RATE = Gauge("task_success_rate", "Task success rate", ["task_type"])
TASK_FAILURE_RATE = Gauge("task_failure_rate", "Task failure rate", ["task_type"])
TASK_TIMEOUT_RATE = Gauge("task_timeout_rate", "Task timeout rate", ["task_type"])

# Security Metrics
AUTHENTICATION_ATTEMPTS = Counter(
    "authentication_attempts_total", "Authentication attempts", ["status"]
)
AUTHORIZATION_FAILURES = Counter(
    "authorization_failures_total", "Authorization failures", ["resource"]
)
RATE_LIMIT_EXCEEDED = Counter(
    "rate_limit_exceeded_total", "Rate limit exceeded", ["endpoint"]
)


# Custom Metrics Collector
class SystemMetricsCollector:
    """Custom metrics collector for system-specific metrics."""

    def __init__(self):
        self.last_network_stats = {}
        self.start_time = time.time()

    def collect(self):
        """Collect system metrics."""
        # System uptime
        SYSTEM_UP.set(1)
        SYSTEM_START_TIME.set(self.start_time)

        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        CPU_USAGE_PERCENT.set(cpu_percent)
        MEMORY_USAGE_BYTES.set(memory.used)
        MEMORY_USAGE_PERCENT.set(memory.percent)

        # Disk usage
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                DISK_USAGE_BYTES.labels(mount_point=partition.mountpoint).set(
                    usage.used
                )
                DISK_USAGE_PERCENT.labels(mount_point=partition.mountpoint).set(
                    usage.percent
                )
            except PermissionError:
                logger.warning(f"Cannot access disk partition: {partition.mountpoint}")

        # Network statistics
        net_io = psutil.net_io_counters(pernic=True)
        for interface, stats in net_io.items():
            if interface in self.last_network_stats:
                last_stats = self.last_network_stats[interface]

                # Calculate deltas
                bytes_sent_delta = stats.bytes_sent - last_stats.bytes_sent
                bytes_recv_delta = stats.bytes_recv - last_stats.bytes_recv
                packets_sent_delta = stats.packets_sent - last_stats.packets_sent
                packets_recv_delta = stats.packets_recv - last_stats.packets_recv

                # Update counters
                NETWORK_BYTES_SENT.labels(interface=interface).inc(bytes_sent_delta)
                NETWORK_BYTES_RECEIVED.labels(interface=interface).inc(bytes_recv_delta)
                NETWORK_PACKETS_SENT.labels(interface=interface).inc(packets_sent_delta)
                NETWORK_PACKETS_RECEIVED.labels(interface=interface).inc(
                    packets_recv_delta
                )

            self.last_network_stats[interface] = stats


# Global metrics collector instance
system_metrics_collector = SystemMetricsCollector()


# Metrics collection functions
async def collect_system_metrics():
    """Collect system metrics asynchronously."""
    while True:
        try:
            system_metrics_collector.collect()
            await asyncio.sleep(15)  # Collect every 15 seconds
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            await asyncio.sleep(30)  # Wait longer on error


def record_task_execution(task_type: str, duration: float, status: str):
    """Record task execution metrics."""
    TASK_EXECUTION_DURATION.labels(task_type=task_type, status=status).observe(duration)
    TASK_PROCESSING_RATE.labels(task_type=task_type, status=status).inc()


def record_database_query(query_type: str, duration: float, success: bool):
    """Record database query metrics."""
    DB_QUERY_DURATION.labels(query_type=query_type).observe(duration)
    if not success:
        DB_QUERY_ERRORS.labels(query_type=query_type).inc()


def record_exception(exception_type: str, module: str):
    """Record exception metrics."""
    EXCEPTION_COUNT.labels(exception_type=exception_type, module=module).inc()


def record_authentication_attempt(status: str):
    """Record authentication attempt metrics."""
    AUTHENTICATION_ATTEMPTS.labels(status=status).inc()


def record_authorization_failure(resource: str):
    """Record authorization failure metrics."""
    AUTHORIZATION_FAILURES.labels(resource=resource).inc()


def record_rate_limit_exceeded(endpoint: str):
    """Record rate limit exceeded metrics."""
    RATE_LIMIT_EXCEEDED.labels(endpoint=endpoint).inc()


# Health check metrics
def update_health_status(healthy: bool):
    """Update system health status."""
    SYSTEM_UP.set(1 if healthy else 0)


def update_task_queue_size(queue_name: str, size: int):
    """Update task queue size metrics."""
    TASK_QUEUE_SIZE.labels(queue_name=queue_name).set(size)


def update_cache_metrics(hit_ratio: float, size: int):
    """Update cache metrics."""
    CACHE_HIT_RATIO.set(hit_ratio)
    CACHE_SIZE.set(size)


def update_task_rates(
    success_rate: float, failure_rate: float, timeout_rate: float, task_type: str
):
    """Update task rate metrics."""
    TASK_SUCCESS_RATE.labels(task_type=task_type).set(success_rate)
    TASK_FAILURE_RATE.labels(task_type=task_type).set(failure_rate)
    TASK_TIMEOUT_RATE.labels(task_type=task_type).set(timeout_rate)
