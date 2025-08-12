"""
OPSVI Docker Management Library

Comprehensive Docker management for the OPSVI ecosystem.
Provides unified access to Docker operations, monitoring, and security.
"""

# Core provider
from .providers.compose_manager import (
    ComposeConfig,
    ComposeError,
    ComposeManager,
    ComposeService,
)

# Manager components
from .providers.container_manager import (
    ContainerConfig,
    ContainerError,
    ContainerInfo,
    ContainerManager,
    ContainerStats,
)
from .providers.docker_provider import DockerConfig, DockerError, DockerProvider
from .providers.image_manager import ImageConfig, ImageError, ImageInfo, ImageManager
from .providers.monitoring import (
    DockerMonitor,
    HealthChecker,
    ResourceMonitor,
    ResourceStats,
)
from .providers.network_manager import (
    NetworkConfig,
    NetworkError,
    NetworkInfo,
    NetworkManager,
)
from .providers.registry_manager import (
    RegistryConfig,
    RegistryError,
    RegistryInfo,
    RegistryManager,
)
from .providers.volume_manager import (
    VolumeConfig,
    VolumeError,
    VolumeInfo,
    VolumeManager,
)

# Schema classes
from .schemas import (
    ComposeDownRequest,
    ComposeServiceRequest,
    ComposeUpRequest,
    ContainerCreateRequest,
    ContainerLogsRequest,
    ContainerUpdateRequest,
    ImageBuildRequest,
    ImagePullRequest,
    ImagePushRequest,
    NetworkConnectRequest,
    NetworkCreateRequest,
    RegistryAuthRequest,
    RegistrySearchRequest,
    VolumeCreateRequest,
    VolumeMountRequest,
)

# Utility classes
from .utils import (
    ContainerUtils,
    DockerUtils,
    HealthUtils,
    ImageUtils,
    MonitoringUtils,
    NetworkUtils,
    SecurityUtils,
    VolumeUtils,
    VulnerabilityScanner,
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
