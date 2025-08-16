"""
Core Docker Provider

Main Docker provider for the OPSVI ecosystem.
Provides comprehensive Docker management capabilities.
"""

import os
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

try:
    import docker
    from docker.errors import DockerException, APIError, ImageNotFound, ContainerError
except ImportError:
    raise ImportError("docker-py is required. Install with `pip install docker`.")

from opsvi_foundation import BaseComponent, ComponentError

logger = logging.getLogger(__name__)


class DockerError(ComponentError):
    """Custom exception for Docker operations."""

    pass


@dataclass
class DockerConfig:
    """Configuration for Docker provider."""

    # Connection settings
    base_url: Optional[str] = None
    timeout: int = 60
    tls: bool = False
    tls_verify: bool = True
    tls_ca_cert: Optional[str] = None
    tls_client_cert: Optional[str] = None
    tls_client_key: Optional[str] = None

    # Registry settings
    registry_url: Optional[str] = None
    registry_username: Optional[str] = None
    registry_password: Optional[str] = None

    # Default settings
    default_network: str = "bridge"
    default_platform: str = "linux/amd64"
    default_pull_policy: str = "if-not-present"

    # Resource limits
    max_containers: int = 100
    max_images: int = 50
    max_networks: int = 20
    max_volumes: int = 30

    # Logging and monitoring
    enable_logging: bool = True
    log_level: str = "INFO"
    enable_monitoring: bool = True
    monitoring_interval: int = 30

    # Security settings
    enable_security_scanning: bool = True
    security_scan_interval: int = 3600  # 1 hour
    enable_vulnerability_checking: bool = True

    # Performance settings
    connection_pool_size: int = 10
    retry_attempts: int = 3
    retry_delay: int = 1

    def __post_init__(self):
        """Set default values from environment variables."""
        self.base_url = self.base_url or os.getenv(
            "DOCKER_HOST", "unix://var/run/docker.sock"
        )
        self.registry_url = self.registry_url or os.getenv("DOCKER_REGISTRY")
        self.registry_username = self.registry_username or os.getenv("DOCKER_USERNAME")
        self.registry_password = self.registry_password or os.getenv("DOCKER_PASSWORD")


class DockerProvider(BaseComponent):
    """
    Comprehensive Docker provider for OPSVI ecosystem.

    Provides full Docker capabilities:
    - Container lifecycle management
    - Image management and registry operations
    - Network and volume management
    - Docker Compose orchestration
    - Health monitoring and resource tracking
    - Security scanning and vulnerability assessment
    """

    def __init__(self, config: DockerConfig, **kwargs: Any) -> None:
        """Initialize Docker provider.

        Args:
            config: Docker configuration
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)

        self.config = config
        self.client = None
        self._managers: Dict[str, Any] = {}

        logger.debug(f"DockerProvider initialized with base_url: {config.base_url}")

    async def initialize(self) -> None:
        """Initialize Docker client and validate connection."""
        try:
            # Create Docker client
            client_kwargs = {
                "base_url": self.config.base_url,
                "timeout": self.config.timeout,
            }

            if self.config.tls:
                client_kwargs["tls"] = docker.tls.TLSConfig(
                    ca_cert=self.config.tls_ca_cert,
                    client_cert=(
                        self.config.tls_client_cert,
                        self.config.tls_client_key,
                    ),
                    verify=self.config.tls_verify,
                )

            self.client = DockerClient(**client_kwargs)

            # Test connection
            self.client.ping()

            # Initialize managers
            await self._initialize_managers()

            logger.info(f"Docker connected: {self.config.base_url}")

        except Exception as e:
            logger.error(f"Docker initialization failed: {e}")
            raise DockerError(f"Failed to initialize Docker provider: {e}")

    async def _initialize_managers(self) -> None:
        """Initialize all Docker managers."""
        from .container_manager import ContainerManager
        from .image_manager import ImageManager
        from .network_manager import NetworkManager
        from .volume_manager import VolumeManager
        from .compose_manager import ComposeManager
        from .registry_manager import RegistryManager
        from .monitoring import DockerMonitor

        # Initialize managers
        self._managers["container"] = ContainerManager(self.client, self.config)
        self._managers["image"] = ImageManager(self.client, self.config)
        self._managers["network"] = NetworkManager(self.client, self.config)
        self._managers["volume"] = VolumeManager(self.client, self.config)
        self._managers["compose"] = ComposeManager(self.client, self.config)
        self._managers["registry"] = RegistryManager(self.client, self.config)
        self._managers["monitor"] = DockerMonitor(self.client, self.config)

        # Initialize each manager
        for manager in self._managers.values():
            if hasattr(manager, "initialize"):
                await manager.initialize()

    async def cleanup(self) -> None:
        """Clean up Docker provider resources."""
        try:
            # Clean up managers
            for manager in self._managers.values():
                if hasattr(manager, "cleanup"):
                    await manager.cleanup()

            # Close Docker client
            if self.client:
                self.client.close()
                self.client = None

            logger.info("Docker provider cleaned up")

        except Exception as e:
            logger.error(f"Docker cleanup failed: {e}")
            raise DockerError(f"Failed to cleanup Docker provider: {e}")

    @property
    def containers(self) -> "ContainerManager":
        """Get container manager."""
        return self._managers["container"]

    @property
    def images(self) -> "ImageManager":
        """Get image manager."""
        return self._managers["image"]

    @property
    def networks(self) -> "NetworkManager":
        """Get network manager."""
        return self._managers["network"]

    @property
    def volumes(self) -> "VolumeManager":
        """Get volume manager."""
        return self._managers["volume"]

    @property
    def compose(self) -> "ComposeManager":
        """Get compose manager."""
        return self._managers["compose"]

    @property
    def registry(self) -> "RegistryManager":
        """Get registry manager."""
        return self._managers["registry"]

    @property
    def monitor(self) -> "DockerMonitor":
        """Get Docker monitor."""
        return self._managers["monitor"]

    async def _health_check_impl(self) -> Dict[str, Any]:
        """Implement health check for Docker provider."""
        try:
            if not self.client:
                return {"success": False, "error": "Docker client not initialized"}

            # Test Docker daemon
            info = self.client.info()

            # Get basic statistics
            containers = self.client.containers.list(all=True)
            images = self.client.images.list()
            networks = self.client.networks.list()
            volumes = self.client.volumes.list()

            return {
                "success": True,
                "docker_version": info.get("ServerVersion", "unknown"),
                "api_version": info.get("ApiVersion", "unknown"),
                "containers": len(containers),
                "images": len(images),
                "networks": len(networks),
                "volumes": len(volumes),
                "system_info": {
                    "architecture": info.get("Architecture", "unknown"),
                    "os": info.get("OperatingSystem", "unknown"),
                    "kernel": info.get("KernelVersion", "unknown"),
                    "cpus": info.get("NCPU", 0),
                    "memory": info.get("MemTotal", 0),
                },
            }

        except Exception as e:
            logger.error(f"Docker health check failed: {e}")
            return {"success": False, "error": str(e)}

    def get_docker_info(self) -> Dict[str, Any]:
        """Get comprehensive Docker system information."""
        try:
            if not self.client:
                raise DockerError("Docker client not initialized")

            info = self.client.info()
            version = self.client.version()

            return {
                "success": True,
                "info": info,
                "version": version,
                "system_stats": {
                    "containers": len(self.client.containers.list(all=True)),
                    "images": len(self.client.images.list()),
                    "networks": len(self.client.networks.list()),
                    "volumes": len(self.client.volumes.list()),
                },
            }

        except Exception as e:
            logger.error(f"Failed to get Docker info: {e}")
            return {"success": False, "error": str(e)}

    def get_manager(self, manager_type: str) -> Any:
        """Get a specific manager by type."""
        if manager_type not in self._managers:
            raise DockerError(f"Unknown manager type: {manager_type}")

        return self._managers[manager_type]

    def list_managers(self) -> List[str]:
        """List all available managers."""
        return list(self._managers.keys())

    async def execute_docker_command(
        self, command: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """Execute a Docker command and return results."""
        try:
            if not self.client:
                raise DockerError("Docker client not initialized")

            # Parse command and execute
            if command == "ps":
                containers = self.client.containers.list(**kwargs)
                return {
                    "success": True,
                    "containers": [container.attrs for container in containers],
                }
            elif command == "images":
                images = self.client.images.list(**kwargs)
                return {"success": True, "images": [image.attrs for image in images]}
            elif command == "networks":
                networks = self.client.networks.list(**kwargs)
                return {
                    "success": True,
                    "networks": [network.attrs for network in networks],
                }
            elif command == "volumes":
                volumes = self.client.volumes.list(**kwargs)
                return {
                    "success": True,
                    "volumes": [volume.attrs for volume in volumes],
                }
            else:
                raise DockerError(f"Unknown Docker command: {command}")

        except Exception as e:
            logger.error(f"Docker command '{command}' failed: {e}")
            return {"success": False, "error": str(e)}
