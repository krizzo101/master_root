"""
OPSVI Docker Management Library

Comprehensive Docker management for the OPSVI ecosystem.
Provides unified access to Docker operations, monitoring, and security.
"""

# Core provider
from .providers.docker_provider import DockerProvider, DockerConfig, DockerError

# Manager components
from .providers.container_manager import (
    ContainerManager,
    ContainerConfig,
    ContainerInfo,
    ContainerStats,
    ContainerError,
)
from .providers.image_manager import ImageManager, ImageConfig, ImageInfo, ImageError
from .providers.network_manager import (
    NetworkManager,
    NetworkConfig,
    NetworkInfo,
    NetworkError,
)
from .providers.volume_manager import (
    VolumeManager,
    VolumeConfig,
    VolumeInfo,
    VolumeError,
)
from .providers.compose_manager import (
    ComposeManager,
    ComposeConfig,
    ComposeService,
    ComposeError,
)
from .providers.registry_manager import (
    RegistryManager,
    RegistryConfig,
    RegistryInfo,
    RegistryError,
)
from .providers.monitoring import (
    DockerMonitor,
    HealthChecker,
    ResourceMonitor,
    ResourceStats,
)

# Utility classes
from .utils import (
    DockerUtils,
    ContainerUtils,
    ImageUtils,
    NetworkUtils,
    VolumeUtils,
    HealthUtils,
    MonitoringUtils,
    SecurityUtils,
    VulnerabilityScanner,
)

# Schema classes
from .schemas import (
    ContainerCreateRequest,
    ContainerUpdateRequest,
    ContainerLogsRequest,
    ImageBuildRequest,
    ImagePullRequest,
    ImagePushRequest,
    NetworkCreateRequest,
    NetworkConnectRequest,
    VolumeCreateRequest,
    VolumeMountRequest,
    ComposeUpRequest,
    ComposeDownRequest,
    ComposeServiceRequest,
    RegistryAuthRequest,
    RegistrySearchRequest,
)

__version__ = "1.0.0"
__author__ = "OPSVI Team"
__description__ = "Comprehensive Docker management for the OPSVI ecosystem"

__all__ = [
    # Core provider
    "DockerProvider",
    "DockerConfig",
    "DockerError",
    # Manager components
    "ContainerManager",
    "ContainerConfig",
    "ContainerInfo",
    "ContainerStats",
    "ContainerError",
    "ImageManager",
    "ImageConfig",
    "ImageInfo",
    "ImageError",
    "NetworkManager",
    "NetworkConfig",
    "NetworkInfo",
    "NetworkError",
    "VolumeManager",
    "VolumeConfig",
    "VolumeInfo",
    "VolumeError",
    "ComposeManager",
    "ComposeConfig",
    "ComposeService",
    "ComposeError",
    "RegistryManager",
    "RegistryConfig",
    "RegistryInfo",
    "RegistryError",
    "DockerMonitor",
    "HealthChecker",
    "ResourceMonitor",
    "ResourceStats",
    # Utility classes
    "DockerUtils",
    "ContainerUtils",
    "ImageUtils",
    "NetworkUtils",
    "VolumeUtils",
    "HealthUtils",
    "MonitoringUtils",
    "SecurityUtils",
    "VulnerabilityScanner",
    # Schema classes
    "ContainerCreateRequest",
    "ContainerUpdateRequest",
    "ContainerLogsRequest",
    "ImageBuildRequest",
    "ImagePullRequest",
    "ImagePushRequest",
    "NetworkCreateRequest",
    "NetworkConnectRequest",
    "VolumeCreateRequest",
    "VolumeMountRequest",
    "ComposeUpRequest",
    "ComposeDownRequest",
    "ComposeServiceRequest",
    "RegistryAuthRequest",
    "RegistrySearchRequest",
]
