"""
Network Manager

Docker network management for the OPSVI ecosystem.
Provides comprehensive network operations and configuration.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime

from docker import DockerClient
from docker.errors import DockerException, APIError, NotFound

from opsvi_foundation import BaseComponent, ComponentError

logger = logging.getLogger(__name__)


class NetworkError(ComponentError):
    """Custom exception for network operations."""

    pass


@dataclass
class NetworkConfig:
    """Configuration for network operations."""

    # Basic settings
    name: str = ""
    driver: str = "bridge"

    # Network settings
    subnet: Optional[str] = None
    gateway: Optional[str] = None
    ip_range: Optional[str] = None
    aux_address: Optional[str] = None

    # Advanced settings
    internal: bool = False
    enable_ipv6: bool = False
    attachable: bool = False
    ingress: bool = False

    # Labels and metadata
    labels: Dict[str, str] = field(default_factory=dict)

    # Driver options
    driver_opts: Dict[str, str] = field(default_factory=dict)

    # IPAM configuration
    ipam_config: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class NetworkInfo:
    """Network information and configuration."""

    id: str
    name: str
    driver: str
    scope: str
    created: datetime
    labels: Dict[str, str]
    ipam_config: List[Dict[str, Any]]
    containers: Dict[str, Dict[str, Any]]
    options: Dict[str, str]

    # Additional metadata
    internal: bool
    enable_ipv6: bool
    attachable: bool
    ingress: bool


class NetworkManager(BaseComponent):
    """
    Comprehensive network management for OPSVI ecosystem.

    Provides full network capabilities:
    - Network creation and configuration
    - Container network connectivity
    - Network inspection and monitoring
    - IPAM management
    - Network security and isolation
    """

    def __init__(self, client: DockerClient, config: Any, **kwargs: Any) -> None:
        """Initialize network manager.

        Args:
            client: Docker client instance
            config: Docker configuration
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)

        self.client = client
        self.config = config
        self._networks: Dict[str, Any] = {}

        logger.debug("NetworkManager initialized")

    async def initialize(self) -> None:
        """Initialize network manager."""
        try:
            # Load existing networks
            networks = self.client.networks.list()
            for network in networks:
                self._networks[network.id] = network

            logger.info(f"NetworkManager initialized with {len(networks)} networks")

        except Exception as e:
            logger.error(f"NetworkManager initialization failed: {e}")
            raise NetworkError(f"Failed to initialize NetworkManager: {e}")

    async def create_network(self, config: NetworkConfig) -> NetworkInfo:
        """Create a new network.

        Args:
            config: Network configuration

        Returns:
            NetworkInfo: Information about the created network
        """
        try:
            # Prepare IPAM configuration
            ipam_config = []
            if config.subnet or config.gateway or config.ip_range or config.aux_address:
                ipam_subnet = {}
                if config.subnet:
                    ipam_subnet["subnet"] = config.subnet
                if config.gateway:
                    ipam_subnet["gateway"] = config.gateway
                if config.ip_range:
                    ipam_subnet["ip_range"] = config.ip_range
                if config.aux_address:
                    ipam_subnet["aux_address"] = config.aux_address
                ipam_config.append(ipam_subnet)

            # Create network
            network = self.client.networks.create(
                name=config.name,
                driver=config.driver,
                internal=config.internal,
                enable_ipv6=config.enable_ipv6,
                attachable=config.attachable,
                ingress=config.ingress,
                labels=config.labels,
                driver_opts=config.driver_opts,
                ipam={"driver": "default", "config": ipam_config or config.ipam_config},
            )

            # Store network reference
            self._networks[network.id] = network

            # Get network info
            network_info = await self.get_network_info(network.id)

            logger.info(f"Network created: {network.id} ({config.name})")
            return network_info

        except Exception as e:
            logger.error(f"Failed to create network: {e}")
            raise NetworkError(f"Network creation failed: {e}")

    async def remove_network(self, network_id: str, force: bool = False) -> bool:
        """Remove a network.

        Args:
            network_id: Network ID or name
            force: Force removal

        Returns:
            bool: True if network removed successfully
        """
        try:
            network = self._get_network(network_id)
            network.remove(force=force)

            # Remove from tracking
            if network.id in self._networks:
                del self._networks[network.id]

            logger.info(f"Network removed: {network_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove network {network_id}: {e}")
            raise NetworkError(f"Network removal failed: {e}")

    async def connect_container(
        self,
        network_id: str,
        container_id: str,
        ipv4_address: Optional[str] = None,
        ipv6_address: Optional[str] = None,
        aliases: Optional[List[str]] = None,
    ) -> bool:
        """Connect a container to a network.

        Args:
            network_id: Network ID or name
            container_id: Container ID or name
            ipv4_address: IPv4 address for container
            ipv6_address: IPv6 address for container
            aliases: Network aliases for container

        Returns:
            bool: True if container connected successfully
        """
        try:
            network = self._get_network(network_id)

            # Prepare endpoint configuration
            endpoint_config = {}
            if ipv4_address or ipv6_address or aliases:
                endpoint_config = {"IPAMConfig": {}}
                if ipv4_address:
                    endpoint_config["IPAMConfig"]["IPv4Address"] = ipv4_address
                if ipv6_address:
                    endpoint_config["IPAMConfig"]["IPv6Address"] = ipv6_address
                if aliases:
                    endpoint_config["IPAMConfig"]["Aliases"] = aliases

            network.connect(container_id, **endpoint_config)

            logger.info(f"Container {container_id} connected to network {network_id}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to connect container {container_id} to network {network_id}: {e}"
            )
            raise NetworkError(f"Container connection failed: {e}")

    async def disconnect_container(
        self, network_id: str, container_id: str, force: bool = False
    ) -> bool:
        """Disconnect a container from a network.

        Args:
            network_id: Network ID or name
            container_id: Container ID or name
            force: Force disconnection

        Returns:
            bool: True if container disconnected successfully
        """
        try:
            network = self._get_network(network_id)
            network.disconnect(container_id, force=force)

            logger.info(
                f"Container {container_id} disconnected from network {network_id}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to disconnect container {container_id} from network {network_id}: {e}"
            )
            raise NetworkError(f"Container disconnection failed: {e}")

    async def get_network_info(self, network_id: str) -> NetworkInfo:
        """Get detailed network information.

        Args:
            network_id: Network ID or name

        Returns:
            NetworkInfo: Network information
        """
        try:
            network = self._get_network(network_id)
            attrs = network.attrs

            return NetworkInfo(
                id=attrs["Id"],
                name=attrs["Name"],
                driver=attrs["Driver"],
                scope=attrs["Scope"],
                created=datetime.fromisoformat(attrs["Created"].replace("Z", "+00:00")),
                labels=attrs["Labels"],
                ipam_config=attrs["IPAM"]["Config"],
                containers=attrs["Containers"],
                options=attrs["Options"],
                internal=attrs["Internal"],
                enable_ipv6=attrs["EnableIPv6"],
                attachable=attrs["Attachable"],
                ingress=attrs["Ingress"],
            )

        except Exception as e:
            logger.error(f"Failed to get network info for {network_id}: {e}")
            raise NetworkError(f"Failed to get network info: {e}")

    async def list_networks(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[NetworkInfo]:
        """List networks.

        Args:
            filters: Filter networks

        Returns:
            List[NetworkInfo]: List of network information
        """
        try:
            networks = self.client.networks.list(filters=filters)

            network_infos = []
            for network in networks:
                try:
                    info = await self.get_network_info(network.id)
                    network_infos.append(info)
                except Exception as e:
                    logger.warning(f"Failed to get info for network {network.id}: {e}")

            return network_infos

        except Exception as e:
            logger.error(f"Failed to list networks: {e}")
            raise NetworkError(f"Failed to list networks: {e}")

    async def inspect_network(self, network_id: str) -> Dict[str, Any]:
        """Inspect network details.

        Args:
            network_id: Network ID or name

        Returns:
            Dict: Network inspection details
        """
        try:
            network = self._get_network(network_id)
            return network.attrs

        except Exception as e:
            logger.error(f"Failed to inspect network {network_id}: {e}")
            raise NetworkError(f"Network inspection failed: {e}")

    async def prune_networks(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Remove unused networks.

        Args:
            filters: Filter networks to prune

        Returns:
            Dict: Prune results
        """
        try:
            result = self.client.networks.prune(filters=filters)

            # Remove from tracking
            for network_id in result.get("NetworksDeleted", []):
                if network_id in self._networks:
                    del self._networks[network_id]

            logger.info(
                f"Networks pruned: {len(result.get('NetworksDeleted', []))} removed"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to prune networks: {e}")
            raise NetworkError(f"Network pruning failed: {e}")

    async def get_network_containers(
        self, network_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """Get containers connected to a network.

        Args:
            network_id: Network ID or name

        Returns:
            Dict: Container information
        """
        try:
            network = self._get_network(network_id)
            network.reload()
            return network.attrs["Containers"]

        except Exception as e:
            logger.error(f"Failed to get containers for network {network_id}: {e}")
            raise NetworkError(f"Failed to get network containers: {e}")

    def _get_network(self, network_id: str) -> Any:
        """Get network by ID or name.

        Args:
            network_id: Network ID or name

        Returns:
            Network: Docker network object
        """
        try:
            # Try to get by ID first
            if network_id in self._networks:
                return self._networks[network_id]

            # Try to get by name
            networks = self.client.networks.list(filters={"name": network_id})
            if networks:
                network = networks[0]
                self._networks[network.id] = network
                return network

            # Try to get by ID from Docker
            try:
                network = self.client.networks.get(network_id)
                self._networks[network.id] = network
                return network
            except:
                pass

            raise NetworkError(f"Network not found: {network_id}")

        except Exception as e:
            logger.error(f"Failed to get network {network_id}: {e}")
            raise NetworkError(f"Failed to get network: {e}")

    async def cleanup(self) -> None:
        """Clean up network manager resources."""
        try:
            # Clear network references
            self._networks.clear()
            logger.info("NetworkManager cleaned up")

        except Exception as e:
            logger.error(f"NetworkManager cleanup failed: {e}")
            raise NetworkError(f"Failed to cleanup NetworkManager: {e}")
