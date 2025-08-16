"""
Compose Manager

Docker Compose management for the OPSVI ecosystem.
Provides comprehensive orchestration and service management.
"""

import logging
import os
import subprocess
import asyncio
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime

from docker import DockerClient
from docker.errors import DockerException, APIError

from opsvi_foundation import BaseComponent, ComponentError

logger = logging.getLogger(__name__)


class ComposeError(ComponentError):
    """Custom exception for compose operations."""

    pass


@dataclass
class ComposeConfig:
    """Configuration for compose operations."""

    # Basic settings
    project_name: str = ""
    project_directory: str = "."

    # Compose files
    compose_files: List[str] = field(default_factory=lambda: ["docker-compose.yml"])

    # Environment settings
    environment: Dict[str, str] = field(default_factory=dict)
    env_file: Optional[str] = None

    # Service settings
    services: List[str] = field(default_factory=list)
    scale: Dict[str, int] = field(default_factory=dict)

    # Build settings
    build: bool = False
    no_build: bool = False
    force_recreate: bool = False
    no_recreate: bool = False

    # Network settings
    network_mode: Optional[str] = None
    networks: List[str] = field(default_factory=list)

    # Volume settings
    volumes: List[str] = field(default_factory=list)

    # Logging settings
    log_level: str = "INFO"
    quiet: bool = False
    verbose: bool = False


@dataclass
class ComposeService:
    """Compose service information."""

    name: str
    image: str
    status: str
    ports: List[str]
    volumes: List[str]
    networks: List[str]
    environment: Dict[str, str]
    depends_on: List[str]
    restart_policy: str
    health_check: Optional[Dict[str, Any]]

    # Runtime information
    container_id: Optional[str] = None
    container_name: Optional[str] = None
    created: Optional[datetime] = None
    state: Optional[str] = None


class ComposeManager(BaseComponent):
    """
    Comprehensive compose management for OPSVI ecosystem.

    Provides full compose capabilities:
    - Compose project lifecycle management
    - Service orchestration and scaling
    - Multi-environment support
    - Health monitoring and recovery
    - Configuration management
    """

    def __init__(self, client: DockerClient, config: Any, **kwargs: Any) -> None:
        """Initialize compose manager.

        Args:
            client: Docker client instance
            config: Docker configuration
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)

        self.client = client
        self.config = config
        self._projects: Dict[str, Any] = {}

        logger.debug("ComposeManager initialized")

    async def initialize(self) -> None:
        """Initialize compose manager."""
        try:
            logger.info("ComposeManager initialized")

        except Exception as e:
            logger.error(f"ComposeManager initialization failed: {e}")
            raise ComposeError(f"Failed to initialize ComposeManager: {e}")

    async def up_project(self, config: ComposeConfig) -> Dict[str, Any]:
        """Start a compose project.

        Args:
            config: Compose configuration

        Returns:
            Dict: Project startup results
        """
        try:
            # Prepare compose command
            cmd = self._build_compose_command(config, "up")

            # Add options
            if config.detach:
                cmd.append("-d")
            if config.build:
                cmd.append("--build")
            if config.force_recreate:
                cmd.append("--force-recreate")
            if config.no_recreate:
                cmd.append("--no-recreate")
            if config.scale:
                for service, replicas in config.scale.items():
                    cmd.extend(["--scale", f"{service}={replicas}"])

            # Add services
            if config.services:
                cmd.extend(config.services)

            # Execute command
            result = await self._execute_compose_command(cmd, config.project_directory)

            logger.info(f"Compose project started: {config.project_name}")
            return result

        except Exception as e:
            logger.error(f"Failed to start compose project: {e}")
            raise ComposeError(f"Compose project startup failed: {e}")

    async def down_project(
        self,
        config: ComposeConfig,
        remove_volumes: bool = False,
        remove_images: bool = False,
        remove_orphans: bool = False,
    ) -> Dict[str, Any]:
        """Stop a compose project.

        Args:
            config: Compose configuration
            remove_volumes: Remove volumes
            remove_images: Remove images
            remove_orphans: Remove orphan containers

        Returns:
            Dict: Project shutdown results
        """
        try:
            # Prepare compose command
            cmd = self._build_compose_command(config, "down")

            # Add options
            if remove_volumes:
                cmd.append("-v")
            if remove_images:
                cmd.append("--rmi")
            if remove_orphans:
                cmd.append("--remove-orphans")

            # Execute command
            result = await self._execute_compose_command(cmd, config.project_directory)

            logger.info(f"Compose project stopped: {config.project_name}")
            return result

        except Exception as e:
            logger.error(f"Failed to stop compose project: {e}")
            raise ComposeError(f"Compose project shutdown failed: {e}")

    async def restart_project(
        self, config: ComposeConfig, services: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Restart a compose project.

        Args:
            config: Compose configuration
            services: Services to restart

        Returns:
            Dict: Project restart results
        """
        try:
            # Prepare compose command
            cmd = self._build_compose_command(config, "restart")

            # Add services
            if services:
                cmd.extend(services)

            # Execute command
            result = await self._execute_compose_command(cmd, config.project_directory)

            logger.info(f"Compose project restarted: {config.project_name}")
            return result

        except Exception as e:
            logger.error(f"Failed to restart compose project: {e}")
            raise ComposeError(f"Compose project restart failed: {e}")

    async def ps_project(self, config: ComposeConfig) -> List[ComposeService]:
        """Get compose project status.

        Args:
            config: Compose configuration

        Returns:
            List[ComposeService]: Service status information
        """
        try:
            # Prepare compose command
            cmd = self._build_compose_command(config, "ps")

            # Execute command
            result = await self._execute_compose_command(cmd, config.project_directory)

            # Parse results
            services = self._parse_ps_output(result.get("output", ""))

            return services

        except Exception as e:
            logger.error(f"Failed to get compose project status: {e}")
            raise ComposeError(f"Failed to get compose project status: {e}")

    async def logs_project(
        self,
        config: ComposeConfig,
        services: Optional[List[str]] = None,
        follow: bool = False,
        tail: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get compose project logs.

        Args:
            config: Compose configuration
            services: Services to get logs for
            follow: Follow log output
            tail: Number of lines to show

        Returns:
            Dict: Log output
        """
        try:
            # Prepare compose command
            cmd = self._build_compose_command(config, "logs")

            # Add options
            if follow:
                cmd.append("-f")
            if tail:
                cmd.extend(["--tail", str(tail)])

            # Add services
            if services:
                cmd.extend(services)

            # Execute command
            result = await self._execute_compose_command(cmd, config.project_directory)

            return result

        except Exception as e:
            logger.error(f"Failed to get compose project logs: {e}")
            raise ComposeError(f"Failed to get compose project logs: {e}")

    async def build_project(
        self,
        config: ComposeConfig,
        services: Optional[List[str]] = None,
        no_cache: bool = False,
        pull: bool = False,
    ) -> Dict[str, Any]:
        """Build compose project images.

        Args:
            config: Compose configuration
            services: Services to build
            no_cache: Don't use cache
            pull: Pull base images

        Returns:
            Dict: Build results
        """
        try:
            # Prepare compose command
            cmd = self._build_compose_command(config, "build")

            # Add options
            if no_cache:
                cmd.append("--no-cache")
            if pull:
                cmd.append("--pull")

            # Add services
            if services:
                cmd.extend(services)

            # Execute command
            result = await self._execute_compose_command(cmd, config.project_directory)

            logger.info(f"Compose project built: {config.project_name}")
            return result

        except Exception as e:
            logger.error(f"Failed to build compose project: {e}")
            raise ComposeError(f"Compose project build failed: {e}")

    async def pull_project(
        self, config: ComposeConfig, services: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Pull compose project images.

        Args:
            config: Compose configuration
            services: Services to pull

        Returns:
            Dict: Pull results
        """
        try:
            # Prepare compose command
            cmd = self._build_compose_command(config, "pull")

            # Add services
            if services:
                cmd.extend(services)

            # Execute command
            result = await self._execute_compose_command(cmd, config.project_directory)

            logger.info(f"Compose project images pulled: {config.project_name}")
            return result

        except Exception as e:
            logger.error(f"Failed to pull compose project images: {e}")
            raise ComposeError(f"Compose project pull failed: {e}")

    async def scale_project(
        self, config: ComposeConfig, scale_config: Dict[str, int]
    ) -> Dict[str, Any]:
        """Scale compose project services.

        Args:
            config: Compose configuration
            scale_config: Service scaling configuration

        Returns:
            Dict: Scale results
        """
        try:
            # Prepare compose command
            cmd = self._build_compose_command(config, "up")
            cmd.append("-d")

            # Add scale options
            for service, replicas in scale_config.items():
                cmd.extend(["--scale", f"{service}={replicas}"])

            # Execute command
            result = await self._execute_compose_command(cmd, config.project_directory)

            logger.info(f"Compose project scaled: {config.project_name}")
            return result

        except Exception as e:
            logger.error(f"Failed to scale compose project: {e}")
            raise ComposeError(f"Compose project scaling failed: {e}")

    async def exec_service(
        self,
        config: ComposeConfig,
        service: str,
        command: List[str],
        user: Optional[str] = None,
        workdir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute command in a compose service.

        Args:
            config: Compose configuration
            service: Service name
            command: Command to execute
            user: User to run as
            workdir: Working directory

        Returns:
            Dict: Execution results
        """
        try:
            # Prepare compose command
            cmd = self._build_compose_command(config, "exec")

            # Add options
            if user:
                cmd.extend(["-u", user])
            if workdir:
                cmd.extend(["-w", workdir])

            # Add service and command
            cmd.append(service)
            cmd.extend(command)

            # Execute command
            result = await self._execute_compose_command(cmd, config.project_directory)

            return result

        except Exception as e:
            logger.error(f"Failed to execute command in compose service: {e}")
            raise ComposeError(f"Compose service execution failed: {e}")

    def _build_compose_command(
        self, config: ComposeConfig, subcommand: str
    ) -> List[str]:
        """Build docker-compose command.

        Args:
            config: Compose configuration
            subcommand: Compose subcommand

        Returns:
            List[str]: Command arguments
        """
        cmd = ["docker-compose"]

        # Add project name
        if config.project_name:
            cmd.extend(["-p", config.project_name])

        # Add compose files
        for compose_file in config.compose_files:
            cmd.extend(["-f", compose_file])

        # Add environment file
        if config.env_file:
            cmd.extend(["--env-file", config.env_file])

        # Add subcommand
        cmd.append(subcommand)

        return cmd

    async def _execute_compose_command(
        self, cmd: List[str], workdir: str
    ) -> Dict[str, Any]:
        """Execute docker-compose command.

        Args:
            cmd: Command to execute
            workdir: Working directory

        Returns:
            Dict: Command results
        """
        try:
            # Set environment variables
            env = os.environ.copy()

            # Execute command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=workdir,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            return {
                "success": process.returncode == 0,
                "return_code": process.returncode,
                "output": stdout.decode("utf-8"),
                "error": stderr.decode("utf-8"),
                "command": " ".join(cmd),
            }

        except Exception as e:
            logger.error(f"Failed to execute compose command: {e}")
            raise ComposeError(f"Compose command execution failed: {e}")

    def _parse_ps_output(self, output: str) -> List[ComposeService]:
        """Parse docker-compose ps output.

        Args:
            output: Command output

        Returns:
            List[ComposeService]: Parsed service information
        """
        services = []

        # Simple parsing - in a real implementation, you'd want more robust parsing
        lines = output.strip().split("\n")

        for line in lines[1:]:  # Skip header
            if line.strip():
                parts = line.split()
                if len(parts) >= 4:
                    service = ComposeService(
                        name=parts[0],
                        image=parts[1],
                        status=parts[2],
                        ports=[],
                        volumes=[],
                        networks=[],
                        environment={},
                        depends_on=[],
                        restart_policy="",
                        health_check=None,
                        container_id=parts[3] if len(parts) > 3 else None,
                        container_name=None,
                        created=None,
                        state=None,
                    )
                    services.append(service)

        return services

    async def cleanup(self) -> None:
        """Clean up compose manager resources."""
        try:
            # Clear project references
            self._projects.clear()
            logger.info("ComposeManager cleaned up")

        except Exception as e:
            logger.error(f"ComposeManager cleanup failed: {e}")
            raise ComposeError(f"Failed to cleanup ComposeManager: {e}")
