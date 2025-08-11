"""
Docker Schemas

Request and response schemas for Docker operations.
Provides structured data models for Docker management operations.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime


# Container Schemas
@dataclass
class ContainerCreateRequest:
    """Request schema for container creation."""

    name: Optional[str] = None
    image: str = ""
    command: Optional[Union[str, List[str]]] = None
    environment: Dict[str, str] = field(default_factory=dict)
    ports: Dict[str, Union[str, int, None]] = field(default_factory=dict)
    volumes: Dict[str, Dict[str, str]] = field(default_factory=dict)
    networks: List[str] = field(default_factory=list)
    restart_policy: Dict[str, str] = field(default_factory=lambda: {"Name": "no"})
    labels: Dict[str, str] = field(default_factory=dict)
    healthcheck: Optional[Dict[str, Any]] = None


@dataclass
class ContainerUpdateRequest:
    """Request schema for container updates."""

    container_id: str
    restart_policy: Optional[Dict[str, str]] = None
    labels: Optional[Dict[str, str]] = None
    environment: Optional[Dict[str, str]] = None


@dataclass
class ContainerLogsRequest:
    """Request schema for container logs."""

    container_id: str
    tail: int = 100
    follow: bool = False
    timestamps: bool = False
    since: Optional[datetime] = None
    until: Optional[datetime] = None


# Image Schemas
@dataclass
class ImageBuildRequest:
    """Request schema for image building."""

    context_path: str = "."
    dockerfile: str = "Dockerfile"
    name: str = ""
    tag: str = "latest"
    build_args: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    platform: Optional[str] = None
    target: Optional[str] = None
    no_cache: bool = False
    pull: bool = False


@dataclass
class ImagePullRequest:
    """Request schema for image pulling."""

    name: str
    tag: str = "latest"
    registry_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    platform: Optional[str] = None


@dataclass
class ImagePushRequest:
    """Request schema for image pushing."""

    name: str
    tag: str = "latest"
    registry_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


# Network Schemas
@dataclass
class NetworkCreateRequest:
    """Request schema for network creation."""

    name: str
    driver: str = "bridge"
    subnet: Optional[str] = None
    gateway: Optional[str] = None
    ip_range: Optional[str] = None
    internal: bool = False
    enable_ipv6: bool = False
    attachable: bool = False
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class NetworkConnectRequest:
    """Request schema for network connection."""

    network_id: str
    container_id: str
    ipv4_address: Optional[str] = None
    ipv6_address: Optional[str] = None
    aliases: Optional[List[str]] = None


# Volume Schemas
@dataclass
class VolumeCreateRequest:
    """Request schema for volume creation."""

    name: str
    driver: str = "local"
    driver_opts: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class VolumeMountRequest:
    """Request schema for volume mounting."""

    volume_name: str
    container_id: str
    mount_path: str
    read_only: bool = False


# Compose Schemas
@dataclass
class ComposeUpRequest:
    """Request schema for compose up."""

    project_name: str
    project_directory: str = "."
    compose_files: List[str] = field(default_factory=lambda: ["docker-compose.yml"])
    services: List[str] = field(default_factory=list)
    build: bool = False
    force_recreate: bool = False
    detach: bool = True
    scale: Dict[str, int] = field(default_factory=dict)


@dataclass
class ComposeDownRequest:
    """Request schema for compose down."""

    project_name: str
    project_directory: str = "."
    compose_files: List[str] = field(default_factory=lambda: ["docker-compose.yml"])
    remove_volumes: bool = False
    remove_images: bool = False
    remove_orphans: bool = False


@dataclass
class ComposeServiceRequest:
    """Request schema for compose service operations."""

    project_name: str
    project_directory: str = "."
    compose_files: List[str] = field(default_factory=lambda: ["docker-compose.yml"])
    service: str
    command: Optional[List[str]] = None
    user: Optional[str] = None
    workdir: Optional[str] = None


# Registry Schemas
@dataclass
class RegistryAuthRequest:
    """Request schema for registry authentication."""

    registry_url: str
    username: str
    password: str
    insecure_registry: bool = False
    verify_tls: bool = True


@dataclass
class RegistrySearchRequest:
    """Request schema for registry search."""

    registry_url: str
    query: str
    limit: int = 25
    filters: Optional[Dict[str, Any]] = None
