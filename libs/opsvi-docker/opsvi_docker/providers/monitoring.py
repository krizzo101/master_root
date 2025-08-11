"""
Docker Monitoring

Comprehensive monitoring and health checking for Docker containers and systems.
Provides real-time monitoring, health checks, and resource tracking.
"""

import logging
import asyncio
import time
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict

from docker import DockerClient
from docker.errors import DockerException, APIError

from opsvi_foundation import BaseComponent, ComponentError

logger = logging.getLogger(__name__)


class MonitoringError(ComponentError):
    """Custom exception for monitoring operations."""

    pass


@dataclass
class HealthCheck:
    """Health check configuration."""

    # Basic settings
    name: str
    check_type: str  # container, image, network, volume, system

    # Check parameters
    target_id: str
    interval: int = 30  # seconds
    timeout: int = 10  # seconds
    retries: int = 3

    # Custom check function
    check_function: Optional[Callable] = None

    # Alerting
    alert_on_failure: bool = True
    alert_threshold: int = 1

    # Status tracking
    last_check: Optional[datetime] = None
    last_status: Optional[str] = None
    consecutive_failures: int = 0


@dataclass
class HealthStatus:
    """Health check status."""

    check_name: str
    target_id: str
    status: str  # healthy, unhealthy, unknown
    timestamp: datetime
    message: str
    details: Dict[str, Any]

    # Metrics
    response_time: Optional[float] = None
    error_count: int = 0


@dataclass
class ResourceMetrics:
    """Resource usage metrics."""

    timestamp: datetime
    container_id: Optional[str] = None

    # CPU metrics
    cpu_usage_percent: float
    cpu_usage_nanos: int
    cpu_limit_nanos: Optional[int] = None

    # Memory metrics
    memory_usage_bytes: int
    memory_limit_bytes: Optional[int] = None
    memory_usage_percent: float

    # Network metrics
    network_rx_bytes: int
    network_tx_bytes: int
    network_rx_packets: int
    network_tx_packets: int

    # Disk metrics
    disk_read_bytes: int
    disk_write_bytes: int
    disk_read_ops: int
    disk_write_ops: int


class DockerMonitor(BaseComponent):
    """
    Comprehensive Docker monitoring for OPSVI ecosystem.

    Provides full monitoring capabilities:
    - Real-time container monitoring
    - System resource tracking
    - Health check management
    - Alert generation and notification
    - Performance metrics collection
    """

    def __init__(self, client: DockerClient, config: Any, **kwargs: Any) -> None:
        """Initialize Docker monitor.

        Args:
            client: Docker client instance
            config: Docker configuration
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)

        self.client = client
        self.config = config
        self._health_checks: Dict[str, HealthCheck] = {}
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._metrics_history: Dict[str, List[ResourceMetrics]] = {}
        self._alert_handlers: List[Callable] = []

        logger.debug("DockerMonitor initialized")

    async def initialize(self) -> None:
        """Initialize Docker monitor."""
        try:
            logger.info("DockerMonitor initialized")

        except Exception as e:
            logger.error(f"DockerMonitor initialization failed: {e}")
            raise MonitoringError(f"Failed to initialize DockerMonitor: {e}")

    async def add_health_check(self, health_check: HealthCheck) -> bool:
        """Add a health check.

        Args:
            health_check: Health check configuration

        Returns:
            bool: True if health check added successfully
        """
        try:
            self._health_checks[health_check.name] = health_check

            # Start monitoring task
            task = asyncio.create_task(self._monitor_health_check(health_check))
            self._monitoring_tasks[health_check.name] = task

            logger.info(f"Health check added: {health_check.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to add health check: {e}")
            raise MonitoringError(f"Failed to add health check: {e}")

    async def remove_health_check(self, check_name: str) -> bool:
        """Remove a health check.

        Args:
            check_name: Health check name

        Returns:
            bool: True if health check removed successfully
        """
        try:
            if check_name in self._health_checks:
                # Cancel monitoring task
                if check_name in self._monitoring_tasks:
                    self._monitoring_tasks[check_name].cancel()
                    del self._monitoring_tasks[check_name]

                del self._health_checks[check_name]
                logger.info(f"Health check removed: {check_name}")
                return True
            else:
                logger.warning(f"Health check not found: {check_name}")
                return False

        except Exception as e:
            logger.error(f"Failed to remove health check {check_name}: {e}")
            raise MonitoringError(f"Failed to remove health check: {e}")

    async def get_health_status(self, check_name: str) -> Optional[HealthStatus]:
        """Get health check status.

        Args:
            check_name: Health check name

        Returns:
            HealthStatus: Health check status
        """
        try:
            if check_name not in self._health_checks:
                return None

            health_check = self._health_checks[check_name]

            # Perform health check
            status = await self._perform_health_check(health_check)
            return status

        except Exception as e:
            logger.error(f"Failed to get health status for {check_name}: {e}")
            raise MonitoringError(f"Failed to get health status: {e}")

    async def get_all_health_statuses(self) -> List[HealthStatus]:
        """Get all health check statuses.

        Returns:
            List[HealthStatus]: All health check statuses
        """
        try:
            statuses = []
            for check_name in self._health_checks:
                status = await self.get_health_status(check_name)
                if status:
                    statuses.append(status)

            return statuses

        except Exception as e:
            logger.error(f"Failed to get all health statuses: {e}")
            raise MonitoringError(f"Failed to get all health statuses: {e}")

    async def start_container_monitoring(
        self, container_id: str, interval: int = 30
    ) -> bool:
        """Start monitoring a container.

        Args:
            container_id: Container ID
            interval: Monitoring interval in seconds

        Returns:
            bool: True if monitoring started successfully
        """
        try:
            # Create monitoring task
            task = asyncio.create_task(self._monitor_container(container_id, interval))
            self._monitoring_tasks[f"container_{container_id}"] = task

            logger.info(f"Container monitoring started: {container_id}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to start container monitoring for {container_id}: {e}"
            )
            raise MonitoringError(f"Failed to start container monitoring: {e}")

    async def stop_container_monitoring(self, container_id: str) -> bool:
        """Stop monitoring a container.

        Args:
            container_id: Container ID

        Returns:
            bool: True if monitoring stopped successfully
        """
        try:
            task_name = f"container_{container_id}"
            if task_name in self._monitoring_tasks:
                self._monitoring_tasks[task_name].cancel()
                del self._monitoring_tasks[task_name]
                logger.info(f"Container monitoring stopped: {container_id}")
                return True
            else:
                logger.warning(f"Container monitoring not found: {container_id}")
                return False

        except Exception as e:
            logger.error(f"Failed to stop container monitoring for {container_id}: {e}")
            raise MonitoringError(f"Failed to stop container monitoring: {e}")

    async def get_container_metrics(
        self, container_id: str, limit: Optional[int] = None
    ) -> List[ResourceMetrics]:
        """Get container metrics history.

        Args:
            container_id: Container ID
            limit: Maximum number of metrics to return

        Returns:
            List[ResourceMetrics]: Container metrics
        """
        try:
            if container_id not in self._metrics_history:
                return []

            metrics = self._metrics_history[container_id]
            if limit:
                metrics = metrics[-limit:]

            return metrics

        except Exception as e:
            logger.error(f"Failed to get container metrics for {container_id}: {e}")
            raise MonitoringError(f"Failed to get container metrics: {e}")

    async def add_alert_handler(self, handler: Callable) -> bool:
        """Add an alert handler.

        Args:
            handler: Alert handler function

        Returns:
            bool: True if handler added successfully
        """
        try:
            self._alert_handlers.append(handler)
            logger.info("Alert handler added")
            return True

        except Exception as e:
            logger.error(f"Failed to add alert handler: {e}")
            raise MonitoringError(f"Failed to add alert handler: {e}")

    async def _monitor_health_check(self, health_check: HealthCheck) -> None:
        """Monitor a health check.

        Args:
            health_check: Health check configuration
        """
        try:
            while True:
                # Perform health check
                status = await self._perform_health_check(health_check)

                # Update health check status
                health_check.last_check = status.timestamp
                health_check.last_status = status.status

                # Handle failures
                if status.status == "unhealthy":
                    health_check.consecutive_failures += 1

                    # Send alert if threshold reached
                    if (
                        health_check.alert_on_failure
                        and health_check.consecutive_failures
                        >= health_check.alert_threshold
                    ):
                        await self._send_alert(health_check, status)
                else:
                    health_check.consecutive_failures = 0

                # Wait for next check
                await asyncio.sleep(health_check.interval)

        except asyncio.CancelledError:
            logger.info(f"Health check monitoring cancelled: {health_check.name}")
        except Exception as e:
            logger.error(f"Health check monitoring failed for {health_check.name}: {e}")

    async def _monitor_container(self, container_id: str, interval: int) -> None:
        """Monitor a container.

        Args:
            container_id: Container ID
            interval: Monitoring interval in seconds
        """
        try:
            while True:
                # Get container stats
                metrics = await self._get_container_metrics(container_id)

                if metrics:
                    # Store metrics
                    if container_id not in self._metrics_history:
                        self._metrics_history[container_id] = []

                    self._metrics_history[container_id].append(metrics)

                    # Keep only recent metrics (last hour)
                    cutoff_time = datetime.now() - timedelta(hours=1)
                    self._metrics_history[container_id] = [
                        m
                        for m in self._metrics_history[container_id]
                        if m.timestamp > cutoff_time
                    ]

                # Wait for next check
                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            logger.info(f"Container monitoring cancelled: {container_id}")
        except Exception as e:
            logger.error(f"Container monitoring failed for {container_id}: {e}")

    async def _perform_health_check(self, health_check: HealthCheck) -> HealthStatus:
        """Perform a health check.

        Args:
            health_check: Health check configuration

        Returns:
            HealthStatus: Health check result
        """
        start_time = time.time()

        try:
            if health_check.check_function:
                # Use custom check function
                result = await health_check.check_function(health_check.target_id)
                status = "healthy" if result else "unhealthy"
                message = "Custom check passed" if result else "Custom check failed"
            else:
                # Use default check based on type
                result = await self._default_health_check(health_check)
                status = result["status"]
                message = result["message"]

            response_time = time.time() - start_time

            return HealthStatus(
                check_name=health_check.name,
                target_id=health_check.target_id,
                status=status,
                timestamp=datetime.now(),
                message=message,
                details=result.get("details", {}),
                response_time=response_time,
            )

        except Exception as e:
            response_time = time.time() - start_time

            return HealthStatus(
                check_name=health_check.name,
                target_id=health_check.target_id,
                status="unhealthy",
                timestamp=datetime.now(),
                message=f"Health check failed: {e}",
                details={"error": str(e)},
                response_time=response_time,
                error_count=1,
            )

    async def _default_health_check(self, health_check: HealthCheck) -> Dict[str, Any]:
        """Perform default health check based on type.

        Args:
            health_check: Health check configuration

        Returns:
            Dict: Health check result
        """
        try:
            if health_check.check_type == "container":
                # Check if container is running
                container = self.client.containers.get(health_check.target_id)
                container.reload()

                if container.status == "running":
                    return {
                        "status": "healthy",
                        "message": "Container is running",
                        "details": {"status": container.status},
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "message": f"Container is not running: {container.status}",
                        "details": {"status": container.status},
                    }

            elif health_check.check_type == "image":
                # Check if image exists
                try:
                    image = self.client.images.get(health_check.target_id)
                    return {
                        "status": "healthy",
                        "message": "Image exists",
                        "details": {"id": image.id},
                    }
                except:
                    return {
                        "status": "unhealthy",
                        "message": "Image not found",
                        "details": {},
                    }

            elif health_check.check_type == "network":
                # Check if network exists
                try:
                    network = self.client.networks.get(health_check.target_id)
                    return {
                        "status": "healthy",
                        "message": "Network exists",
                        "details": {"id": network.id},
                    }
                except:
                    return {
                        "status": "unhealthy",
                        "message": "Network not found",
                        "details": {},
                    }

            elif health_check.check_type == "volume":
                # Check if volume exists
                try:
                    volume = self.client.volumes.get(health_check.target_id)
                    return {
                        "status": "healthy",
                        "message": "Volume exists",
                        "details": {"name": volume.name},
                    }
                except:
                    return {
                        "status": "unhealthy",
                        "message": "Volume not found",
                        "details": {},
                    }

            elif health_check.check_type == "system":
                # Check Docker daemon
                try:
                    info = self.client.info()
                    return {
                        "status": "healthy",
                        "message": "Docker daemon is running",
                        "details": {"version": info.get("ServerVersion")},
                    }
                except:
                    return {
                        "status": "unhealthy",
                        "message": "Docker daemon is not responding",
                        "details": {},
                    }

            else:
                return {
                    "status": "unknown",
                    "message": f"Unknown check type: {health_check.check_type}",
                    "details": {},
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Health check failed: {e}",
                "details": {"error": str(e)},
            }

    async def _get_container_metrics(
        self, container_id: str
    ) -> Optional[ResourceMetrics]:
        """Get container resource metrics.

        Args:
            container_id: Container ID

        Returns:
            ResourceMetrics: Container metrics
        """
        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)

            # Calculate CPU percentage
            cpu_delta = (
                stats["cpu_stats"]["cpu_usage"]["total_usage"]
                - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            )
            system_delta = (
                stats["cpu_stats"]["system_cpu_usage"]
                - stats["precpu_stats"]["system_cpu_usage"]
            )
            cpu_percent = (
                (cpu_delta / system_delta)
                * len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"])
                * 100
            )

            # Calculate memory percentage
            memory_usage = stats["memory_stats"]["usage"]
            memory_limit = stats["memory_stats"]["limit"]
            memory_percent = (
                (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0
            )

            return ResourceMetrics(
                timestamp=datetime.now(),
                container_id=container_id,
                cpu_usage_percent=cpu_percent,
                cpu_usage_nanos=stats["cpu_stats"]["cpu_usage"]["total_usage"],
                cpu_limit_nanos=stats["cpu_stats"].get("cpu_quota"),
                memory_usage_bytes=memory_usage,
                memory_limit_bytes=memory_limit,
                memory_usage_percent=memory_percent,
                network_rx_bytes=stats["networks"].get("eth0", {}).get("rx_bytes", 0),
                network_tx_bytes=stats["networks"].get("eth0", {}).get("tx_bytes", 0),
                network_rx_packets=stats["networks"]
                .get("eth0", {})
                .get("rx_packets", 0),
                network_tx_packets=stats["networks"]
                .get("eth0", {})
                .get("tx_packets", 0),
                disk_read_bytes=stats["blkio_stats"]
                .get("io_service_bytes_recursive", [{}])[0]
                .get("value", 0),
                disk_write_bytes=stats["blkio_stats"]
                .get("io_service_bytes_recursive", [{}])[1]
                .get("value", 0),
                disk_read_ops=stats["blkio_stats"]
                .get("io_serviced_recursive", [{}])[0]
                .get("value", 0),
                disk_write_ops=stats["blkio_stats"]
                .get("io_serviced_recursive", [{}])[1]
                .get("value", 0),
            )

        except Exception as e:
            logger.error(f"Failed to get container metrics for {container_id}: {e}")
            return None

    async def _send_alert(
        self, health_check: HealthCheck, status: HealthStatus
    ) -> None:
        """Send an alert.

        Args:
            health_check: Health check configuration
            status: Health check status
        """
        try:
            alert_data = {
                "check_name": health_check.name,
                "target_id": health_check.target_id,
                "status": status.status,
                "message": status.message,
                "timestamp": status.timestamp,
                "consecutive_failures": health_check.consecutive_failures,
            }

            # Send to all alert handlers
            for handler in self._alert_handlers:
                try:
                    await handler(alert_data)
                except Exception as e:
                    logger.error(f"Alert handler failed: {e}")

            logger.warning(f"Alert sent for health check: {health_check.name}")

        except Exception as e:
            logger.error(f"Failed to send alert: {e}")

    async def cleanup(self) -> None:
        """Clean up Docker monitor resources."""
        try:
            # Cancel all monitoring tasks
            for task in self._monitoring_tasks.values():
                task.cancel()

            # Wait for tasks to complete
            if self._monitoring_tasks:
                await asyncio.gather(
                    *self._monitoring_tasks.values(), return_exceptions=True
                )

            # Clear data structures
            self._health_checks.clear()
            self._monitoring_tasks.clear()
            self._metrics_history.clear()
            self._alert_handlers.clear()

            logger.info("DockerMonitor cleaned up")

        except Exception as e:
            logger.error(f"DockerMonitor cleanup failed: {e}")
            raise MonitoringError(f"Failed to cleanup DockerMonitor: {e}")


class HealthChecker(BaseComponent):
    """
    Health checker for Docker components.

    Provides health checking capabilities for containers, images, networks, and volumes.
    """

    def __init__(self, client: DockerClient, config: Any, **kwargs: Any) -> None:
        """Initialize health checker.

        Args:
            client: Docker client instance
            config: Docker configuration
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)

        self.client = client
        self.config = config

        logger.debug("HealthChecker initialized")

    async def check_container_health(self, container_id: str) -> HealthStatus:
        """Check container health.

        Args:
            container_id: Container ID

        Returns:
            HealthStatus: Health check result
        """
        try:
            container = self.client.containers.get(container_id)
            container.reload()

            if container.status == "running":
                return HealthStatus(
                    check_name="container_health",
                    target_id=container_id,
                    status="healthy",
                    timestamp=datetime.now(),
                    message="Container is running",
                    details={"status": container.status},
                )
            else:
                return HealthStatus(
                    check_name="container_health",
                    target_id=container_id,
                    status="unhealthy",
                    timestamp=datetime.now(),
                    message=f"Container is not running: {container.status}",
                    details={"status": container.status},
                )

        except Exception as e:
            return HealthStatus(
                check_name="container_health",
                target_id=container_id,
                status="unhealthy",
                timestamp=datetime.now(),
                message=f"Container health check failed: {e}",
                details={"error": str(e)},
            )

    async def check_system_health(self) -> HealthStatus:
        """Check Docker system health.

        Returns:
            HealthStatus: Health check result
        """
        try:
            info = self.client.info()

            return HealthStatus(
                check_name="system_health",
                target_id="docker_system",
                status="healthy",
                timestamp=datetime.now(),
                message="Docker system is healthy",
                details={
                    "version": info.get("ServerVersion"),
                    "containers": info.get("Containers", 0),
                    "images": info.get("Images", 0),
                },
            )

        except Exception as e:
            return HealthStatus(
                check_name="system_health",
                target_id="docker_system",
                status="unhealthy",
                timestamp=datetime.now(),
                message=f"Docker system health check failed: {e}",
                details={"error": str(e)},
            )


class ResourceMonitor(BaseComponent):
    """
    Resource monitor for Docker containers and systems.

    Provides resource monitoring capabilities for CPU, memory, network, and disk usage.
    """

    def __init__(self, client: DockerClient, config: Any, **kwargs: Any) -> None:
        """Initialize resource monitor.

        Args:
            client: Docker client instance
            config: Docker configuration
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)

        self.client = client
        self.config = config

        logger.debug("ResourceMonitor initialized")

    async def get_container_resources(self, container_id: str) -> ResourceMetrics:
        """Get container resource usage.

        Args:
            container_id: Container ID

        Returns:
            ResourceMetrics: Container resource metrics
        """
        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)

            # Calculate CPU percentage
            cpu_delta = (
                stats["cpu_stats"]["cpu_usage"]["total_usage"]
                - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            )
            system_delta = (
                stats["cpu_stats"]["system_cpu_usage"]
                - stats["precpu_stats"]["system_cpu_usage"]
            )
            cpu_percent = (
                (cpu_delta / system_delta)
                * len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"])
                * 100
            )

            # Calculate memory percentage
            memory_usage = stats["memory_stats"]["usage"]
            memory_limit = stats["memory_stats"]["limit"]
            memory_percent = (
                (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0
            )

            return ResourceMetrics(
                timestamp=datetime.now(),
                container_id=container_id,
                cpu_usage_percent=cpu_percent,
                cpu_usage_nanos=stats["cpu_stats"]["cpu_usage"]["total_usage"],
                cpu_limit_nanos=stats["cpu_stats"].get("cpu_quota"),
                memory_usage_bytes=memory_usage,
                memory_limit_bytes=memory_limit,
                memory_usage_percent=memory_percent,
                network_rx_bytes=stats["networks"].get("eth0", {}).get("rx_bytes", 0),
                network_tx_bytes=stats["networks"].get("eth0", {}).get("tx_bytes", 0),
                network_rx_packets=stats["networks"]
                .get("eth0", {})
                .get("rx_packets", 0),
                network_tx_packets=stats["networks"]
                .get("eth0", {})
                .get("tx_packets", 0),
                disk_read_bytes=stats["blkio_stats"]
                .get("io_service_bytes_recursive", [{}])[0]
                .get("value", 0),
                disk_write_bytes=stats["blkio_stats"]
                .get("io_service_bytes_recursive", [{}])[1]
                .get("value", 0),
                disk_read_ops=stats["blkio_stats"]
                .get("io_serviced_recursive", [{}])[0]
                .get("value", 0),
                disk_write_ops=stats["blkio_stats"]
                .get("io_serviced_recursive", [{}])[1]
                .get("value", 0),
            )

        except Exception as e:
            logger.error(f"Failed to get container resources for {container_id}: {e}")
            raise MonitoringError(f"Failed to get container resources: {e}")

    async def get_system_resources(self) -> Dict[str, Any]:
        """Get Docker system resource usage.

        Returns:
            Dict: System resource information
        """
        try:
            info = self.client.info()

            return {
                "timestamp": datetime.now(),
                "containers": info.get("Containers", 0),
                "images": info.get("Images", 0),
                "driver": info.get("Driver"),
                "driver_status": info.get("DriverStatus", []),
                "plugins": info.get("Plugins", {}),
                "memory_limit": info.get("MemTotal", 0),
                "swap_limit": info.get("SwapTotal", 0),
                "kernel_memory": info.get("KernelMemory", 0),
                "cpu_count": info.get("NCPU", 0),
                "operating_system": info.get("OperatingSystem"),
                "architecture": info.get("Architecture"),
                "docker_root_dir": info.get("DockerRootDir"),
                "server_version": info.get("ServerVersion"),
            }

        except Exception as e:
            logger.error(f"Failed to get system resources: {e}")
            raise MonitoringError(f"Failed to get system resources: {e}")
