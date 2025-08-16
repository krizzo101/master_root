"""
Docker Utilities

Common Docker operations and utility functions.
"""

import logging
import os
import subprocess
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class DockerUtils:
    """
    Docker utility functions.

    Provides common Docker operations and helpers:
    - Docker command execution
    - Environment validation
    - Configuration helpers
    - System information
    """

    @staticmethod
    def check_docker_installation() -> Dict[str, Any]:
        """Check if Docker is installed and accessible."""
        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True, timeout=10
            )
            return {
                "installed": result.returncode == 0,
                "version": result.stdout.strip() if result.returncode == 0 else None,
                "error": result.stderr if result.returncode != 0 else None,
            }
        except Exception as e:
            return {"installed": False, "version": None, "error": str(e)}

    @staticmethod
    def check_docker_compose_installation() -> Dict[str, Any]:
        """Check if Docker Compose is installed and accessible."""
        try:
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return {
                "installed": result.returncode == 0,
                "version": result.stdout.strip() if result.returncode == 0 else None,
                "error": result.stderr if result.returncode != 0 else None,
            }
        except Exception as e:
            return {"installed": False, "version": None, "error": str(e)}

    @staticmethod
    def execute_docker_command(
        command: List[str], capture_output: bool = True
    ) -> Dict[str, Any]:
        """Execute a Docker command and return results."""
        try:
            result = subprocess.run(
                command, capture_output=capture_output, text=True, timeout=30
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout if capture_output else None,
                "stderr": result.stderr if capture_output else None,
                "return_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": None,
                "stderr": "Command timed out",
                "return_code": -1,
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": None,
                "stderr": str(e),
                "return_code": -1,
            }

    @staticmethod
    def get_docker_system_info() -> Dict[str, Any]:
        """Get comprehensive Docker system information."""
        try:
            # Get Docker info
            info_result = subprocess.run(
                ["docker", "info"], capture_output=True, text=True, timeout=10
            )

            # Get Docker version
            version_result = subprocess.run(
                ["docker", "version"], capture_output=True, text=True, timeout=10
            )

            # Get disk usage
            system_result = subprocess.run(
                ["docker", "system", "df"], capture_output=True, text=True, timeout=10
            )

            return {
                "info": info_result.stdout if info_result.returncode == 0 else None,
                "version": (
                    version_result.stdout if version_result.returncode == 0 else None
                ),
                "disk_usage": (
                    system_result.stdout if system_result.returncode == 0 else None
                ),
                "success": all(
                    r.returncode == 0
                    for r in [info_result, version_result, system_result]
                ),
            }
        except Exception as e:
            return {
                "info": None,
                "version": None,
                "disk_usage": None,
                "success": False,
                "error": str(e),
            }

    @staticmethod
    def validate_dockerfile(dockerfile_path: str) -> Dict[str, Any]:
        """Validate a Dockerfile for syntax and best practices."""
        if not os.path.exists(dockerfile_path):
            return {
                "valid": False,
                "errors": [f"Dockerfile not found: {dockerfile_path}"],
            }

        errors = []
        warnings = []

        try:
            with open(dockerfile_path, "r") as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Basic syntax validation
                if line.startswith("FROM") and " " not in line[4:].strip():
                    errors.append(f"Line {i}: Invalid FROM instruction")

                # Best practices warnings
                if line.startswith("RUN") and "apt-get" in line and "clean" not in line:
                    warnings.append(
                        f"Line {i}: Consider adding 'apt-get clean' to reduce image size"
                    )

                if line.startswith("COPY") and "*" in line:
                    warnings.append(
                        f"Line {i}: Using wildcards in COPY may include unwanted files"
                    )

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "line_count": len(lines),
            }
        except Exception as e:
            return {"valid": False, "errors": [f"Error reading Dockerfile: {str(e)}"]}

    @staticmethod
    def get_docker_environment() -> Dict[str, str]:
        """Get Docker-related environment variables."""
        docker_env = {}
        for key, value in os.environ.items():
            if key.startswith("DOCKER_") or key in [
                "COMPOSE_PROJECT_NAME",
                "COMPOSE_FILE",
            ]:
                docker_env[key] = value
        return docker_env

    @staticmethod
    def format_bytes(bytes_value: int) -> str:
        """Format bytes into human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"

    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration in seconds to human-readable format."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds}s"
        else:
            hours = seconds // 3600
            remaining_minutes = (seconds % 3600) // 60
            return f"{hours}h {remaining_minutes}m"

    @staticmethod
    def parse_docker_image_name(image_name: str) -> Dict[str, str]:
        """Parse a Docker image name into components."""
        parts = image_name.split("/")

        if len(parts) == 1:
            # Just image name (e.g., "nginx")
            return {
                "registry": None,
                "repository": "library",
                "image": parts[0].split(":")[0],
                "tag": parts[0].split(":")[1] if ":" in parts[0] else "latest",
            }
        elif len(parts) == 2:
            # Repository/image (e.g., "user/nginx")
            image_part = parts[1].split(":")
            return {
                "registry": None,
                "repository": parts[0],
                "image": image_part[0],
                "tag": image_part[1] if len(image_part) > 1 else "latest",
            }
        elif len(parts) >= 3:
            # Registry/repository/image (e.g., "docker.io/library/nginx")
            image_part = parts[-1].split(":")
            return {
                "registry": parts[0],
                "repository": "/".join(parts[1:-1]),
                "image": image_part[0],
                "tag": image_part[1] if len(image_part) > 1 else "latest",
            }

        return {
            "registry": None,
            "repository": None,
            "image": image_name,
            "tag": "latest",
        }

    @staticmethod
    def build_docker_image_name(
        name: str, tag: str = "latest", registry: Optional[str] = None
    ) -> str:
        """Build a Docker image name from components."""
        if registry:
            return f"{registry}/{name}:{tag}"
        else:
            return f"{name}:{tag}"

    @staticmethod
    def get_container_logs_since(container_id: str, since: datetime) -> str:
        """Get container logs since a specific time."""
        since_str = since.strftime("%Y-%m-%dT%H:%M:%S")
        result = subprocess.run(
            ["docker", "logs", "--since", since_str, container_id],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout if result.returncode == 0 else result.stderr

    @staticmethod
    def get_container_stats(container_id: str) -> Dict[str, Any]:
        """Get container statistics."""
        result = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "json", container_id],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0 and result.stdout.strip():
            try:
                import json

                return json.loads(result.stdout.strip())
            except json.JSONDecodeError:
                return {"error": "Failed to parse stats JSON"}
        else:
            return {"error": result.stderr or "Failed to get container stats"}
