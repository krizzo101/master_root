"""
Volume Manager

Docker volume management for the OPSVI ecosystem.
Provides comprehensive volume operations and data persistence.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime

from docker import DockerClient
from docker.errors import DockerException, APIError, NotFound

from opsvi_foundation import BaseComponent, ComponentError

logger = logging.getLogger(__name__)


class VolumeError(ComponentError):
    """Custom exception for volume operations."""

    pass


@dataclass
class VolumeConfig:
    """Configuration for volume operations."""

    # Basic settings
    name: str = ""
    driver: str = "local"

    # Driver options
    driver_opts: Dict[str, str] = field(default_factory=dict)

    # Labels and metadata
    labels: Dict[str, str] = field(default_factory=dict)

    # Mount options
    mount_point: Optional[str] = None
    read_only: bool = False

    # Advanced settings
    autobackup: bool = False
    backup_retention: int = 7


@dataclass
class VolumeInfo:
    """Volume information and configuration."""

    name: str
    driver: str
    mountpoint: str
    created: datetime
    status: Dict[str, Any]
    labels: Dict[str, str]
    scope: str
    options: Dict[str, str]

    # Additional metadata
    size: Optional[int] = None
    usage_data: Optional[Dict[str, Any]] = None


class VolumeManager(BaseComponent):
    """
    Comprehensive volume management for OPSVI ecosystem.

    Provides full volume capabilities:
    - Volume creation and configuration
    - Volume mounting and unmounting
    - Volume inspection and monitoring
    - Data persistence and backup
    - Volume cleanup and optimization
    """

    def __init__(self, client: DockerClient, config: Any, **kwargs: Any) -> None:
        """Initialize volume manager.

        Args:
            client: Docker client instance
            config: Docker configuration
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)

        self.client = client
        self.config = config
        self._volumes: Dict[str, Any] = {}

        logger.debug("VolumeManager initialized")

    async def initialize(self) -> None:
        """Initialize volume manager."""
        try:
            # Load existing volumes
            volumes = self.client.volumes.list()
            for volume in volumes:
                self._volumes[volume.name] = volume

            logger.info(f"VolumeManager initialized with {len(volumes)} volumes")

        except Exception as e:
            logger.error(f"VolumeManager initialization failed: {e}")
            raise VolumeError(f"Failed to initialize VolumeManager: {e}")

    async def create_volume(self, config: VolumeConfig) -> VolumeInfo:
        """Create a new volume.

        Args:
            config: Volume configuration

        Returns:
            VolumeInfo: Information about the created volume
        """
        try:
            # Create volume
            volume = self.client.volumes.create(
                name=config.name,
                driver=config.driver,
                driver_opts=config.driver_opts,
                labels=config.labels,
            )

            # Store volume reference
            self._volumes[volume.name] = volume

            # Get volume info
            volume_info = await self.get_volume_info(volume.name)

            logger.info(f"Volume created: {volume.name}")
            return volume_info

        except Exception as e:
            logger.error(f"Failed to create volume: {e}")
            raise VolumeError(f"Volume creation failed: {e}")

    async def remove_volume(self, volume_name: str, force: bool = False) -> bool:
        """Remove a volume.

        Args:
            volume_name: Volume name
            force: Force removal

        Returns:
            bool: True if volume removed successfully
        """
        try:
            volume = self._get_volume(volume_name)
            volume.remove(force=force)

            # Remove from tracking
            if volume.name in self._volumes:
                del self._volumes[volume.name]

            logger.info(f"Volume removed: {volume_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove volume {volume_name}: {e}")
            raise VolumeError(f"Volume removal failed: {e}")

    async def get_volume_info(self, volume_name: str) -> VolumeInfo:
        """Get detailed volume information.

        Args:
            volume_name: Volume name

        Returns:
            VolumeInfo: Volume information
        """
        try:
            volume = self._get_volume(volume_name)
            attrs = volume.attrs

            return VolumeInfo(
                name=attrs["Name"],
                driver=attrs["Driver"],
                mountpoint=attrs["Mountpoint"],
                created=datetime.fromisoformat(
                    attrs["CreatedAt"].replace("Z", "+00:00")
                ),
                status=attrs.get("Status", {}),
                labels=attrs.get("Labels", {}),
                scope=attrs.get("Scope", "local"),
                options=attrs.get("Options", {}),
                size=(
                    attrs.get("UsageData", {}).get("Size")
                    if attrs.get("UsageData")
                    else None
                ),
                usage_data=attrs.get("UsageData"),
            )

        except Exception as e:
            logger.error(f"Failed to get volume info for {volume_name}: {e}")
            raise VolumeError(f"Failed to get volume info: {e}")

    async def list_volumes(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[VolumeInfo]:
        """List volumes.

        Args:
            filters: Filter volumes

        Returns:
            List[VolumeInfo]: List of volume information
        """
        try:
            volumes = self.client.volumes.list(filters=filters)

            volume_infos = []
            for volume in volumes:
                try:
                    info = await self.get_volume_info(volume.name)
                    volume_infos.append(info)
                except Exception as e:
                    logger.warning(f"Failed to get info for volume {volume.name}: {e}")

            return volume_infos

        except Exception as e:
            logger.error(f"Failed to list volumes: {e}")
            raise VolumeError(f"Failed to list volumes: {e}")

    async def inspect_volume(self, volume_name: str) -> Dict[str, Any]:
        """Inspect volume details.

        Args:
            volume_name: Volume name

        Returns:
            Dict: Volume inspection details
        """
        try:
            volume = self._get_volume(volume_name)
            return volume.attrs

        except Exception as e:
            logger.error(f"Failed to inspect volume {volume_name}: {e}")
            raise VolumeError(f"Volume inspection failed: {e}")

    async def prune_volumes(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Remove unused volumes.

        Args:
            filters: Filter volumes to prune

        Returns:
            Dict: Prune results
        """
        try:
            result = self.client.volumes.prune(filters=filters)

            # Remove from tracking
            for volume_name in result.get("VolumesDeleted", []):
                if volume_name in self._volumes:
                    del self._volumes[volume_name]

            logger.info(
                f"Volumes pruned: {len(result.get('VolumesDeleted', []))} removed"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to prune volumes: {e}")
            raise VolumeError(f"Volume pruning failed: {e}")

    async def mount_volume(
        self,
        volume_name: str,
        container_id: str,
        mount_path: str,
        read_only: bool = False,
    ) -> bool:
        """Mount a volume to a container.

        Args:
            volume_name: Volume name
            container_id: Container ID or name
            mount_path: Mount path in container
            read_only: Mount as read-only

        Returns:
            bool: True if volume mounted successfully
        """
        try:
            # Get container
            container = self.client.containers.get(container_id)

            # Prepare mount configuration
            mount_config = {
                "Type": "volume",
                "Source": volume_name,
                "Target": mount_path,
                "ReadOnly": read_only,
            }

            # Update container with new mount
            container.update(mounts=[mount_config])

            logger.info(
                f"Volume {volume_name} mounted to container {container_id} at {mount_path}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to mount volume {volume_name} to container {container_id}: {e}"
            )
            raise VolumeError(f"Volume mounting failed: {e}")

    async def unmount_volume(self, volume_name: str, container_id: str) -> bool:
        """Unmount a volume from a container.

        Args:
            volume_name: Volume name
            container_id: Container ID or name

        Returns:
            bool: True if volume unmounted successfully
        """
        try:
            # Get container
            container = self.client.containers.get(container_id)

            # Get current mounts and remove the specified volume
            current_mounts = container.attrs.get("Mounts", [])
            new_mounts = [
                mount for mount in current_mounts if mount.get("Source") != volume_name
            ]

            # Update container with new mount configuration
            container.update(mounts=new_mounts)

            logger.info(f"Volume {volume_name} unmounted from container {container_id}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to unmount volume {volume_name} from container {container_id}: {e}"
            )
            raise VolumeError(f"Volume unmounting failed: {e}")

    async def get_volume_usage(self, volume_name: str) -> Dict[str, Any]:
        """Get volume usage statistics.

        Args:
            volume_name: Volume name

        Returns:
            Dict: Volume usage information
        """
        try:
            volume = self._get_volume(volume_name)
            volume.reload()

            usage_data = volume.attrs.get("UsageData", {})
            return {
                "size": usage_data.get("Size"),
                "ref_count": usage_data.get("RefCount"),
                "volume_name": volume_name,
            }

        except Exception as e:
            logger.error(f"Failed to get usage for volume {volume_name}: {e}")
            raise VolumeError(f"Failed to get volume usage: {e}")

    async def backup_volume(self, volume_name: str, backup_path: str) -> bool:
        """Create a backup of a volume.

        Args:
            volume_name: Volume name
            backup_path: Backup file path

        Returns:
            bool: True if backup created successfully
        """
        try:
            # Create a temporary container to backup the volume
            container = self.client.containers.run(
                image="alpine:latest",
                command=f"tar -czf /backup/volume_backup.tar.gz -C /data .",
                volumes={
                    volume_name: {"bind": "/data", "mode": "ro"},
                    backup_path: {"bind": "/backup", "mode": "rw"},
                },
                detach=True,
                remove=True,
            )

            # Wait for container to complete
            result = container.wait()

            if result["StatusCode"] == 0:
                logger.info(f"Volume backup created: {volume_name} -> {backup_path}")
                return True
            else:
                raise VolumeError(
                    f"Backup failed with exit code: {result['StatusCode']}"
                )

        except Exception as e:
            logger.error(f"Failed to backup volume {volume_name}: {e}")
            raise VolumeError(f"Volume backup failed: {e}")

    async def restore_volume(self, volume_name: str, backup_path: str) -> bool:
        """Restore a volume from backup.

        Args:
            volume_name: Volume name
            backup_path: Backup file path

        Returns:
            bool: True if restore completed successfully
        """
        try:
            # Create a temporary container to restore the volume
            container = self.client.containers.run(
                image="alpine:latest",
                command=f"tar -xzf /backup/volume_backup.tar.gz -C /data",
                volumes={
                    volume_name: {"bind": "/data", "mode": "rw"},
                    backup_path: {"bind": "/backup", "mode": "ro"},
                },
                detach=True,
                remove=True,
            )

            # Wait for container to complete
            result = container.wait()

            if result["StatusCode"] == 0:
                logger.info(f"Volume restored: {backup_path} -> {volume_name}")
                return True
            else:
                raise VolumeError(
                    f"Restore failed with exit code: {result['StatusCode']}"
                )

        except Exception as e:
            logger.error(f"Failed to restore volume {volume_name}: {e}")
            raise VolumeError(f"Volume restore failed: {e}")

    def _get_volume(self, volume_name: str) -> Any:
        """Get volume by name.

        Args:
            volume_name: Volume name

        Returns:
            Volume: Docker volume object
        """
        try:
            # Try to get from tracking first
            if volume_name in self._volumes:
                return self._volumes[volume_name]

            # Try to get from Docker
            volume = self.client.volumes.get(volume_name)
            self._volumes[volume.name] = volume
            return volume

        except Exception as e:
            logger.error(f"Failed to get volume {volume_name}: {e}")
            raise VolumeError(f"Failed to get volume: {e}")

    async def cleanup(self) -> None:
        """Clean up volume manager resources."""
        try:
            # Clear volume references
            self._volumes.clear()
            logger.info("VolumeManager cleaned up")

        except Exception as e:
            logger.error(f"VolumeManager cleanup failed: {e}")
            raise VolumeError(f"Failed to cleanup VolumeManager: {e}")
