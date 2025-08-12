"""
Image Manager

Docker image management for the OPSVI ecosystem.
Provides comprehensive image operations and registry management.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, BinaryIO

from docker import DockerClient
from opsvi_foundation import BaseComponent, ComponentError

logger = logging.getLogger(__name__)


class ImageError(ComponentError):
    """Custom exception for image operations."""

    pass


@dataclass
class ImageConfig:
    """Configuration for image operations."""

    # Basic settings
    name: str = ""
    tag: str = "latest"
    repository: str | None = None

    # Build settings
    dockerfile: str = "Dockerfile"
    context_path: str = "."
    build_args: dict[str, str] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)

    # Registry settings
    registry_url: str | None = None
    username: str | None = None
    password: str | None = None

    # Pull settings
    pull_policy: str = "if-not-present"  # always, if-not-present, never

    # Security settings
    platform: str | None = None
    security_opt: list[str] = field(default_factory=list)

    # Build optimization
    cache_from: list[str] = field(default_factory=list)
    target: str | None = None
    network_mode: str | None = None

    # Output settings
    quiet: bool = False
    rm: bool = True
    forcerm: bool = False


@dataclass
class ImageInfo:
    """Image information and metadata."""

    id: str
    tags: list[str]
    size: int
    created: datetime
    architecture: str
    os: str
    variant: str | None
    digest: str | None
    labels: dict[str, str]
    config: dict[str, Any]
    layers: list[str]

    # Additional metadata
    parent: str | None = None
    comment: str | None = None
    author: str | None = None
    repo_digests: list[str] = field(default_factory=list)


class ImageManager(BaseComponent):
    """
    Comprehensive image management for OPSVI ecosystem.

    Provides full image capabilities:
    - Image building and creation
    - Image pulling and pushing
    - Image tagging and management
    - Registry operations
    - Image inspection and metadata
    - Layer analysis and optimization
    """

    def __init__(self, client: DockerClient, config: Any, **kwargs: Any) -> None:
        """Initialize image manager.

        Args:
            client: Docker client instance
            config: Docker configuration
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)

        self.client = client
        self.config = config
        self._images: dict[str, Any] = {}

        logger.debug("ImageManager initialized")

    async def initialize(self) -> None:
        """Initialize image manager."""
        try:
            # Load existing images
            images = self.client.images.list()
            for image in images:
                self._images[image.id] = image

            logger.info(f"ImageManager initialized with {len(images)} images")

        except Exception as e:
            logger.error(f"ImageManager initialization failed: {e}")
            raise ImageError(f"Failed to initialize ImageManager: {e}")

    async def build_image(
        self, config: ImageConfig, fileobj: BinaryIO | None = None
    ) -> ImageInfo:
        """Build a Docker image.

        Args:
            config: Image configuration
            fileobj: Optional file object for build context

        Returns:
            ImageInfo: Information about the built image
        """
        try:
            # Prepare build arguments
            build_kwargs = {
                "path": config.context_path,
                "dockerfile": config.dockerfile,
                "buildargs": config.build_args,
                "labels": config.labels,
                "platform": config.platform,
                "target": config.target,
                "network_mode": config.network_mode,
                "cache_from": config.cache_from,
                "rm": config.rm,
                "forcerm": config.forcerm,
                "quiet": config.quiet,
            }

            # Add fileobj if provided
            if fileobj:
                build_kwargs["fileobj"] = fileobj
                build_kwargs["custom_context"] = True

            # Build image
            build_result = self.client.images.build(**build_kwargs)

            # Get the last image from build result
            image = None
            for line in build_result:
                if "stream" in line:
                    logger.info(line["stream"].strip())
                if "aux" in line and "ID" in line["aux"]:
                    image_id = line["aux"]["ID"]
                    image = self.client.images.get(image_id)
                    break

            if not image:
                raise ImageError("Failed to build image - no image ID returned")

            # Tag image if name specified
            if config.name:
                full_name = f"{config.name}:{config.tag}"
                image.tag(config.name, tag=config.tag)
                logger.info(f"Image tagged as: {full_name}")

            # Store image reference
            self._images[image.id] = image

            # Get image info
            image_info = await self.get_image_info(image.id)

            logger.info(f"Image built successfully: {image.id}")
            return image_info

        except Exception as e:
            logger.error(f"Failed to build image: {e}")
            raise ImageError(f"Image build failed: {e}")

    async def pull_image(self, config: ImageConfig) -> ImageInfo:
        """Pull an image from registry.

        Args:
            config: Image configuration

        Returns:
            ImageInfo: Information about the pulled image
        """
        try:
            # Construct image name
            image_name = config.name
            if config.repository:
                image_name = f"{config.repository}/{image_name}"
            if config.registry_url:
                image_name = f"{config.registry_url}/{image_name}"

            full_name = f"{image_name}:{config.tag}"

            # Pull image
            logger.info(f"Pulling image: {full_name}")
            image = self.client.images.pull(
                repository=full_name, tag=config.tag, platform=config.platform
            )

            # Store image reference
            self._images[image.id] = image

            # Get image info
            image_info = await self.get_image_info(image.id)

            logger.info(f"Image pulled successfully: {image.id}")
            return image_info

        except Exception as e:
            logger.error(f"Failed to pull image {config.name}:{config.tag}: {e}")
            raise ImageError(f"Image pull failed: {e}")

    async def push_image(self, config: ImageConfig) -> bool:
        """Push an image to registry.

        Args:
            config: Image configuration

        Returns:
            bool: True if image pushed successfully
        """
        try:
            # Get image
            image = self._get_image(config.name, config.tag)

            # Construct image name
            image_name = config.name
            if config.repository:
                image_name = f"{config.repository}/{image_name}"
            if config.registry_url:
                image_name = f"{config.registry_url}/{image_name}"

            full_name = f"{image_name}:{config.tag}"

            # Tag image for push
            image.tag(image_name, tag=config.tag)

            # Push image
            logger.info(f"Pushing image: {full_name}")
            push_result = self.client.images.push(
                repository=full_name, tag=config.tag, stream=True, decode=True
            )

            # Process push result
            for line in push_result:
                if "error" in line:
                    raise ImageError(f"Push failed: {line['error']}")
                if "status" in line:
                    logger.info(f"Push status: {line['status']}")

            logger.info(f"Image pushed successfully: {full_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to push image {config.name}:{config.tag}: {e}")
            raise ImageError(f"Image push failed: {e}")

    async def tag_image(
        self, source_image: str, target_name: str, target_tag: str = "latest"
    ) -> bool:
        """Tag an image.

        Args:
            source_image: Source image ID or name
            target_name: Target image name
            target_tag: Target image tag

        Returns:
            bool: True if image tagged successfully
        """
        try:
            image = self._get_image_by_id_or_name(source_image)
            image.tag(target_name, tag=target_tag)

            logger.info(f"Image tagged: {source_image} -> {target_name}:{target_tag}")
            return True

        except Exception as e:
            logger.error(f"Failed to tag image {source_image}: {e}")
            raise ImageError(f"Image tag failed: {e}")

    async def remove_image(
        self, image_id: str, force: bool = False, noprune: bool = False
    ) -> bool:
        """Remove an image.

        Args:
            image_id: Image ID or name
            force: Force removal
            noprune: Don't delete untagged parents

        Returns:
            bool: True if image removed successfully
        """
        try:
            image = self._get_image_by_id_or_name(image_id)
            self.client.images.remove(image.id, force=force, noprune=noprune)

            # Remove from tracking
            if image.id in self._images:
                del self._images[image.id]

            logger.info(f"Image removed: {image_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove image {image_id}: {e}")
            raise ImageError(f"Image removal failed: {e}")

    async def get_image_info(self, image_id: str) -> ImageInfo:
        """Get detailed image information.

        Args:
            image_id: Image ID or name

        Returns:
            ImageInfo: Image information
        """
        try:
            image = self._get_image_by_id_or_name(image_id)
            attrs = image.attrs

            return ImageInfo(
                id=attrs["Id"],
                tags=attrs["RepoTags"] if attrs["RepoTags"] else [],
                size=attrs["Size"],
                created=datetime.fromisoformat(attrs["Created"].replace("Z", "+00:00")),
                architecture=attrs["Architecture"],
                os=attrs["Os"],
                variant=attrs.get("Variant"),
                digest=(
                    attrs.get("RepoDigests", [None])[0]
                    if attrs.get("RepoDigests")
                    else None
                ),
                labels=attrs["Config"]["Labels"],
                config=attrs["Config"],
                layers=attrs["Layers"],
                parent=attrs.get("Parent"),
                comment=attrs.get("Comment"),
                author=attrs.get("Author"),
                repo_digests=attrs.get("RepoDigests", []),
            )

        except Exception as e:
            logger.error(f"Failed to get image info for {image_id}: {e}")
            raise ImageError(f"Failed to get image info: {e}")

    async def list_images(
        self, filters: dict[str, Any] | None = None, all_images: bool = False
    ) -> list[ImageInfo]:
        """List images.

        Args:
            filters: Filter images
            all_images: Include intermediate images

        Returns:
            List[ImageInfo]: List of image information
        """
        try:
            images = self.client.images.list(filters=filters, all=all_images)

            image_infos = []
            for image in images:
                try:
                    info = await self.get_image_info(image.id)
                    image_infos.append(info)
                except Exception as e:
                    logger.warning(f"Failed to get info for image {image.id}: {e}")

            return image_infos

        except Exception as e:
            logger.error(f"Failed to list images: {e}")
            raise ImageError(f"Failed to list images: {e}")

    async def search_images(
        self, term: str, limit: int = 25, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Search for images in registry.

        Args:
            term: Search term
            limit: Maximum number of results
            filters: Search filters

        Returns:
            List[Dict]: Search results
        """
        try:
            results = self.client.images.search(term, limit=limit, filters=filters)
            return results

        except Exception as e:
            logger.error(f"Failed to search images for '{term}': {e}")
            raise ImageError(f"Image search failed: {e}")

    async def save_image(self, image_id: str, output_path: str) -> bool:
        """Save an image to a tar file.

        Args:
            image_id: Image ID or name
            output_path: Output file path

        Returns:
            bool: True if image saved successfully
        """
        try:
            image = self._get_image_by_id_or_name(image_id)

            with open(output_path, "wb") as f:
                for chunk in image.save():
                    f.write(chunk)

            logger.info(f"Image saved to: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save image {image_id}: {e}")
            raise ImageError(f"Image save failed: {e}")

    async def load_image(self, input_path: str) -> ImageInfo:
        """Load an image from a tar file.

        Args:
            input_path: Input file path

        Returns:
            ImageInfo: Information about the loaded image
        """
        try:
            with open(input_path, "rb") as f:
                images = self.client.images.load(f)

            if not images:
                raise ImageError("No images found in tar file")

            image = images[0]

            # Store image reference
            self._images[image.id] = image

            # Get image info
            image_info = await self.get_image_info(image.id)

            logger.info(f"Image loaded successfully: {image.id}")
            return image_info

        except Exception as e:
            logger.error(f"Failed to load image from {input_path}: {e}")
            raise ImageError(f"Image load failed: {e}")

    async def get_image_history(self, image_id: str) -> list[dict[str, Any]]:
        """Get image history.

        Args:
            image_id: Image ID or name

        Returns:
            List[Dict]: Image history
        """
        try:
            image = self._get_image_by_id_or_name(image_id)
            history = image.history()
            return history

        except Exception as e:
            logger.error(f"Failed to get image history for {image_id}: {e}")
            raise ImageError(f"Failed to get image history: {e}")

    async def inspect_image(self, image_id: str) -> dict[str, Any]:
        """Inspect image details.

        Args:
            image_id: Image ID or name

        Returns:
            Dict: Image inspection details
        """
        try:
            image = self._get_image_by_id_or_name(image_id)
            return image.attrs

        except Exception as e:
            logger.error(f"Failed to inspect image {image_id}: {e}")
            raise ImageError(f"Image inspection failed: {e}")

    def _get_image(self, name: str, tag: str = "latest") -> Any:
        """Get image by name and tag.

        Args:
            name: Image name
            tag: Image tag

        Returns:
            Image: Docker image object
        """
        try:
            full_name = f"{name}:{tag}"
            image = self.client.images.get(full_name)
            self._images[image.id] = image
            return image

        except Exception as e:
            logger.error(f"Failed to get image {name}:{tag}: {e}")
            raise ImageError(f"Failed to get image: {e}")

    def _get_image_by_id_or_name(self, image_id: str) -> Any:
        """Get image by ID or name.

        Args:
            image_id: Image ID or name

        Returns:
            Image: Docker image object
        """
        try:
            # Try to get by ID first
            if image_id in self._images:
                return self._images[image_id]

            # Try to get by ID from Docker
            try:
                image = self.client.images.get(image_id)
                self._images[image.id] = image
                return image
            except:
                pass

            # Try to get by name
            images = self.client.images.list(filters={"reference": image_id})
            if images:
                image = images[0]
                self._images[image.id] = image
                return image

            raise ImageError(f"Image not found: {image_id}")

        except Exception as e:
            logger.error(f"Failed to get image {image_id}: {e}")
            raise ImageError(f"Failed to get image: {e}")

    async def cleanup(self) -> None:
        """Clean up image manager resources."""
        try:
            # Clear image references
            self._images.clear()
            logger.info("ImageManager cleaned up")

        except Exception as e:
            logger.error(f"ImageManager cleanup failed: {e}")
            raise ImageError(f"Failed to cleanup ImageManager: {e}")
