"""
Docker Schemas

Request and response schemas for Docker operations.
Provides structured data models for Docker management operations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


# Container Schemas
@dataclass
class ContainerCreateRequest:
    """Request schema for container creation."""

    name: str | None = None
    image: str = ""
    command: str | list[str] | None = None
    environment: dict[str, str] = field(default_factory=dict)
    ports: dict[str, str | int | None] = field(default_factory=dict)
    volumes: dict[str, dict[str, str]] = field(default_factory=dict)
    networks: list[str] = field(default_factory=list)
    restart_policy: dict[str, str] = field(default_factory=lambda: {"Name": "no"})
    labels: dict[str, str] = field(default_factory=dict)
    healthcheck: dict[str, Any] | None = None


@dataclass
class ContainerUpdateRequest:
    """Request schema for container updates."""

    container_id: str
    restart_policy: dict[str, str] | None = None
    labels: dict[str, str] | None = None
    environment: dict[str, str] | None = None


@dataclass
class ContainerLogsRequest:
    """Request schema for container logs."""

    container_id: str
    tail: int = 100
    follow: bool = False
    timestamps: bool = False
    since: datetime | None = None
    until: datetime | None = None


# Image Schemas
@dataclass
class ImageBuildRequest:
    """Request schema for image building."""

    context_path: str = "."
    dockerfile: str = "Dockerfile"
    name: str = ""
    tag: str = "latest"
    build_args: dict[str, str] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)
    platform: str | None = None
    target: str | None = None
    no_cache: bool = False
    pull: bool = False


@dataclass
class ImagePullRequest:
    """Request schema for image pulling."""

    name: str
    tag: str = "latest"
    registry_url: str | None = None
    username: str | None = None
    password: str | None = None
    platform: str | None = None


@dataclass
class ImagePushRequest:
    """Request schema for image pushing."""

    name: str
    tag: str = "latest"
    registry_url: str | None = None
    username: str | None = None
    password: str | None = None


# Network Schemas
@dataclass
class NetworkCreateRequest:
    """Request schema for network creation."""

    name: str
    driver: str = "bridge"
    subnet: str | None = None
    gateway: str | None = None
    ip_range: str | None = None
    internal: bool = False
    enable_ipv6: bool = False
    attachable: bool = False
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class NetworkConnectRequest:
    """Request schema for network connection."""

    network_id: str
    container_id: str
    ipv4_address: str | None = None
    ipv6_address: str | None = None
    aliases: list[str] | None = None


# Volume Schemas
@dataclass
class VolumeCreateRequest:
    """Request schema for volume creation."""

    name: str
    driver: str = "local"
    driver_opts: dict[str, str] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)


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
    compose_files: list[str] = field(default_factory=lambda: ["docker-compose.yml"])
    services: list[str] = field(default_factory=list)
    build: bool = False
    force_recreate: bool = False
    detach: bool = True
    scale: dict[str, int] = field(default_factory=dict)


@dataclass
class ComposeDownRequest:
    """Request schema for compose down."""

    project_name: str
    project_directory: str = "."
    compose_files: list[str] = field(default_factory=lambda: ["docker-compose.yml"])
    remove_volumes: bool = False
    remove_images: bool = False
    remove_orphans: bool = False


@dataclass
class ComposeServiceRequest:
    """Request schema for compose service operations."""

    project_name: str
    project_directory: str = "."
    compose_files: list[str] = field(default_factory=lambda: ["docker-compose.yml"])
    service: str
    command: list[str] | None = None
    user: str | None = None
    workdir: str | None = None


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
    filters: dict[str, Any] | None = None
