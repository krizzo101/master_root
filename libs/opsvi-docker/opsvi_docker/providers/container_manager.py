"""
Container Manager

Docker container lifecycle management for the OPSVI ecosystem.
Provides comprehensive container operations and monitoring.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime

from docker import DockerClient
from docker.errors import DockerException, APIError, ImageNotFound, ContainerError

from opsvi_foundation import BaseComponent, ComponentError

logger = logging.getLogger(__name__)


class ContainerError(ComponentError):
    """Custom exception for container operations."""

    pass


@dataclass
class ContainerConfig:
    """Configuration for container operations."""

    # Basic settings
    name: Optional[str] = None
    image: str = ""
    command: Optional[Union[str, List[str]]] = None
    entrypoint: Optional[Union[str, List[str]]] = None

    # Environment and working directory
    environment: Dict[str, str] = field(default_factory=dict)
    working_dir: Optional[str] = None

    # Port mappings
    ports: Dict[str, Union[str, int, None]] = field(default_factory=dict)
    publish_all_ports: bool = False

    # Volume mounts
    volumes: Dict[str, Dict[str, str]] = field(default_factory=dict)
    binds: List[str] = field(default_factory=list)

    # Network settings
    network_mode: Optional[str] = None
    networks: List[str] = field(default_factory=list)

    # Resource limits
    cpu_quota: Optional[int] = None
    cpu_period: Optional[int] = None
    mem_limit: Optional[str] = None
    memswap_limit: Optional[str] = None

    # Security settings
    user: Optional[str] = None
    privileged: bool = False
    read_only: bool = False
    security_opt: List[str] = field(default_factory=list)

    # Restart policy
    restart_policy: Dict[str, str] = field(default_factory=lambda: {"Name": "no"})

    # Health check
    healthcheck: Optional[Dict[str, Any]] = None

    # Labels and metadata
    labels: Dict[str, str] = field(default_factory=dict)

    # Auto-remove and detach
    auto_remove: bool = False
    detach: bool = True

    # Logging
    log_config: Optional[Dict[str, Any]] = None


@dataclass
class ContainerInfo:
    """Container information and status."""

    id: str
    name: str
    image: str
    status: str
    state: str
    created: datetime
    ports: Dict[str, List[Dict[str, str]]]
    labels: Dict[str, str]
    network_settings: Dict[str, Any]
    mounts: List[Dict[str, Any]]
    config: Dict[str, Any]
    host_config: Dict[str, Any]

    # Runtime information
    cpu_usage: Optional[float] = None
    memory_usage: Optional[int] = None
    network_io: Optional[Dict[str, int]] = None
    disk_io: Optional[Dict[str, int]] = None


@dataclass
class ContainerStats:
    """Container resource usage statistics."""

    container_id: str
    timestamp: datetime

    # CPU statistics
    cpu_percent: float
    cpu_usage: int
    cpu_system_usage: int
    cpu_throttling_data: Dict[str, int]

    # Memory statistics
    memory_usage: int
    memory_max_usage: int
    memory_limit: int
    memory_percent: float

    # Network statistics
    network_rx_bytes: int
    network_tx_bytes: int
    network_rx_packets: int
    network_tx_packets: int

    # Disk statistics
    disk_read_bytes: int
    disk_write_bytes: int
    disk_read_ops: int
    disk_write_ops: int


class ContainerManager(BaseComponent):
    """
    Comprehensive container management for OPSVI ecosystem.

    Provides full container capabilities:
    - Container lifecycle management (create, start, stop, remove)
    - Container monitoring and statistics
    - Log management and streaming
    - Health checks and status monitoring
    - Resource usage tracking
    - Container inspection and configuration
    """

    def __init__(self, client: DockerClient, config: Any, **kwargs: Any) -> None:
        """Initialize container manager.

        Args:
            client: Docker client instance
            config: Docker configuration
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)

        self.client = client
        self.config = config
        self._containers: Dict[str, Any] = {}

        logger.debug("ContainerManager initialized")

    async def initialize(self) -> None:
        """Initialize container manager."""
        try:
            # Load existing containers
            containers = self.client.containers.list(all=True)
            for container in containers:
                self._containers[container.id] = container

            logger.info(
                f"ContainerManager initialized with {len(containers)} containers"
            )

        except Exception as e:
            logger.error(f"ContainerManager initialization failed: {e}")
            raise ContainerError(f"Failed to initialize ContainerManager: {e}")

    async def create_container(self, config: ContainerConfig) -> ContainerInfo:
        """Create a new container.

        Args:
            config: Container configuration

        Returns:
            ContainerInfo: Information about the created container
        """
        try:
            # Prepare container configuration
            container_config = {
                "image": config.image,
                "command": config.command,
                "entrypoint": config.entrypoint,
                "environment": config.environment,
                "working_dir": config.working_dir,
                "ports": config.ports,
                "volumes": config.volumes,
                "network_mode": config.network_mode,
                "user": config.user,
                "privileged": config.privileged,
                "read_only": config.read_only,
                "security_opt": config.security_opt,
                "restart_policy": config.restart_policy,
                "healthcheck": config.healthcheck,
                "labels": config.labels,
                "log_config": config.log_config,
            }

            # Prepare host configuration
            host_config = self.client.api.create_host_config(
                binds=config.binds,
                port_bindings=config.ports,
                publish_all_ports=config.publish_all_ports,
                cpu_quota=config.cpu_quota,
                cpu_period=config.cpu_period,
                mem_limit=config.mem_limit,
                memswap_limit=config.memswap_limit,
                restart_policy=config.restart_policy,
                auto_remove=config.auto_remove,
                read_only=config.read_only,
                security_opt=config.security_opt,
            )

            # Create container
            container = self.client.containers.create(
                name=config.name,
                **container_config,
                host_config=host_config,
                detach=config.detach,
            )

            # Store container reference
            self._containers[container.id] = container

            # Get container info
            container_info = await self.get_container_info(container.id)

            logger.info(
                f"Container created: {container.id} ({config.name or 'unnamed'})"
            )
            return container_info

        except Exception as e:
            logger.error(f"Failed to create container: {e}")
            raise ContainerError(f"Container creation failed: {e}")

    async def start_container(self, container_id: str) -> bool:
        """Start a container.

        Args:
            container_id: Container ID or name

        Returns:
            bool: True if container started successfully
        """
        try:
            container = self._get_container(container_id)
            container.start()

            logger.info(f"Container started: {container_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to start container {container_id}: {e}")
            raise ContainerError(f"Container start failed: {e}")

    async def stop_container(self, container_id: str, timeout: int = 10) -> bool:
        """Stop a container.

        Args:
            container_id: Container ID or name
            timeout: Timeout in seconds

        Returns:
            bool: True if container stopped successfully
        """
        try:
            container = self._get_container(container_id)
            container.stop(timeout=timeout)

            logger.info(f"Container stopped: {container_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to stop container {container_id}: {e}")
            raise ContainerError(f"Container stop failed: {e}")

    async def restart_container(self, container_id: str, timeout: int = 10) -> bool:
        """Restart a container.

        Args:
            container_id: Container ID or name
            timeout: Timeout in seconds

        Returns:
            bool: True if container restarted successfully
        """
        try:
            container = self._get_container(container_id)
            container.restart(timeout=timeout)

            logger.info(f"Container restarted: {container_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to restart container {container_id}: {e}")
            raise ContainerError(f"Container restart failed: {e}")

    async def remove_container(
        self, container_id: str, force: bool = False, volumes: bool = False
    ) -> bool:
        """Remove a container.

        Args:
            container_id: Container ID or name
            force: Force removal even if running
            volumes: Remove associated volumes

        Returns:
            bool: True if container removed successfully
        """
        try:
            container = self._get_container(container_id)
            container.remove(force=force, volumes=volumes)

            # Remove from tracking
            if container.id in self._containers:
                del self._containers[container.id]

            logger.info(f"Container removed: {container_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove container {container_id}: {e}")
            raise ContainerError(f"Container removal failed: {e}")

    async def get_container_info(self, container_id: str) -> ContainerInfo:
        """Get detailed container information.

        Args:
            container_id: Container ID or name

        Returns:
            ContainerInfo: Container information
        """
        try:
            container = self._get_container(container_id)
            attrs = container.attrs

            return ContainerInfo(
                id=attrs["Id"],
                name=attrs["Name"].lstrip("/"),
                image=attrs["Config"]["Image"],
                status=attrs["State"]["Status"],
                state=attrs["State"]["State"],
                created=datetime.fromisoformat(attrs["Created"].replace("Z", "+00:00")),
                ports=attrs["NetworkSettings"]["Ports"],
                labels=attrs["Config"]["Labels"],
                network_settings=attrs["NetworkSettings"],
                mounts=attrs["Mounts"],
                config=attrs["Config"],
                host_config=attrs["HostConfig"],
            )

        except Exception as e:
            logger.error(f"Failed to get container info for {container_id}: {e}")
            raise ContainerError(f"Failed to get container info: {e}")

    async def get_container_stats(self, container_id: str) -> ContainerStats:
        """Get container resource usage statistics.

        Args:
            container_id: Container ID or name

        Returns:
            ContainerStats: Container statistics
        """
        try:
            container = self._get_container(container_id)
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

            return ContainerStats(
                container_id=container_id,
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                cpu_usage=stats["cpu_stats"]["cpu_usage"]["total_usage"],
                cpu_system_usage=stats["cpu_stats"]["system_cpu_usage"],
                cpu_throttling_data=stats["cpu_stats"].get("throttling_data", {}),
                memory_usage=memory_usage,
                memory_max_usage=stats["memory_stats"].get("max_usage", 0),
                memory_limit=memory_limit,
                memory_percent=memory_percent,
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
            logger.error(f"Failed to get container stats for {container_id}: {e}")
            raise ContainerError(f"Failed to get container stats: {e}")

    async def get_container_logs(
        self, container_id: str, tail: int = 100, follow: bool = False
    ) -> str:
        """Get container logs.

        Args:
            container_id: Container ID or name
            tail: Number of lines to return
            follow: Follow log output

        Returns:
            str: Container logs
        """
        try:
            container = self._get_container(container_id)
            logs = container.logs(tail=tail, follow=follow, stream=False)

            return logs.decode("utf-8")

        except Exception as e:
            logger.error(f"Failed to get container logs for {container_id}: {e}")
            raise ContainerError(f"Failed to get container logs: {e}")

    async def execute_command(
        self,
        container_id: str,
        command: Union[str, List[str]],
        user: Optional[str] = None,
        privileged: bool = False,
    ) -> Dict[str, Any]:
        """Execute a command in a running container.

        Args:
            container_id: Container ID or name
            command: Command to execute
            user: User to run command as
            privileged: Run in privileged mode

        Returns:
            Dict: Command execution result
        """
        try:
            container = self._get_container(container_id)
            exec_result = container.exec_run(
                cmd=command, user=user, privileged=privileged
            )

            return {
                "exit_code": exec_result.exit_code,
                "output": exec_result.output.decode("utf-8"),
                "success": exec_result.exit_code == 0,
            }

        except Exception as e:
            logger.error(f"Failed to execute command in container {container_id}: {e}")
            raise ContainerError(f"Command execution failed: {e}")

    async def list_containers(
        self, all_containers: bool = False, filters: Optional[Dict[str, Any]] = None
    ) -> List[ContainerInfo]:
        """List containers.

        Args:
            all_containers: Include stopped containers
            filters: Filter containers

        Returns:
            List[ContainerInfo]: List of container information
        """
        try:
            containers = self.client.containers.list(
                all=all_containers, filters=filters
            )

            container_infos = []
            for container in containers:
                try:
                    info = await self.get_container_info(container.id)
                    container_infos.append(info)
                except Exception as e:
                    logger.warning(
                        f"Failed to get info for container {container.id}: {e}"
                    )

            return container_infos

        except Exception as e:
            logger.error(f"Failed to list containers: {e}")
            raise ContainerError(f"Failed to list containers: {e}")

    async def get_container_status(self, container_id: str) -> str:
        """Get container status.

        Args:
            container_id: Container ID or name

        Returns:
            str: Container status
        """
        try:
            container = self._get_container(container_id)
            container.reload()
            return container.status

        except Exception as e:
            logger.error(f"Failed to get container status for {container_id}: {e}")
            raise ContainerError(f"Failed to get container status: {e}")

    async def wait_for_container(
        self, container_id: str, timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Wait for container to finish.

        Args:
            container_id: Container ID or name
            timeout: Timeout in seconds

        Returns:
            Dict: Wait result
        """
        try:
            container = self._get_container(container_id)
            result = container.wait(timeout=timeout)

            return {
                "exit_code": result["StatusCode"],
                "error": result.get("Error", {}).get("Message", ""),
                "success": result["StatusCode"] == 0,
            }

        except Exception as e:
            logger.error(f"Failed to wait for container {container_id}: {e}")
            raise ContainerError(f"Failed to wait for container: {e}")

    def _get_container(self, container_id: str) -> Any:
        """Get container by ID or name.

        Args:
            container_id: Container ID or name

        Returns:
            Container: Docker container object
        """
        try:
            # Try to get by ID first
            if container_id in self._containers:
                return self._containers[container_id]

            # Try to get by name
            containers = self.client.containers.list(
                all=True, filters={"name": container_id}
            )
            if containers:
                container = containers[0]
                self._containers[container.id] = container
                return container

            # Try to get by ID from Docker
            try:
                container = self.client.containers.get(container_id)
                self._containers[container.id] = container
                return container
            except:
                pass

            raise ContainerError(f"Container not found: {container_id}")

        except Exception as e:
            logger.error(f"Failed to get container {container_id}: {e}")
            raise ContainerError(f"Failed to get container: {e}")

    async def cleanup(self) -> None:
        """Clean up container manager resources."""
        try:
            # Clear container references
            self._containers.clear()
            logger.info("ContainerManager cleaned up")

        except Exception as e:
            logger.error(f"ContainerManager cleanup failed: {e}")
            raise ContainerError(f"Failed to cleanup ContainerManager: {e}")
