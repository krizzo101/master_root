"""
Image Utilities

Image-specific utility functions and helpers.
"""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class ImageUtils:
    """
    Image utility functions.

    Provides image-specific operations and helpers:
    - Image analysis and optimization
    - Image size calculation
    - Layer analysis
    """

    @staticmethod
    def analyze_image_layers(image_info: dict[str, Any]) -> dict[str, Any]:
        """Analyze Docker image layers for optimization opportunities."""
        analysis = {
            "total_layers": 0,
            "layer_sizes": [],
            "large_layers": [],
            "optimization_opportunities": [],
            "total_size": 0,
        }

        layers = image_info.get("Layers", [])
        analysis["total_layers"] = len(layers)

        # Analyze layer sizes
        for i, layer in enumerate(layers):
            layer_size = layer.get("Size", 0)
            analysis["total_size"] += layer_size
            analysis["layer_sizes"].append(
                {
                    "layer_index": i,
                    "size": layer_size,
                    "size_formatted": ImageUtils.format_image_size(layer_size),
                }
            )

            # Identify large layers (>100MB)
            if layer_size > 100 * 1024 * 1024:  # 100MB
                analysis["large_layers"].append(
                    {
                        "layer_index": i,
                        "size": layer_size,
                        "size_formatted": ImageUtils.format_image_size(layer_size),
                    }
                )

        # Generate optimization recommendations
        if analysis["total_layers"] > 10:
            analysis["optimization_opportunities"].append(
                "Consider reducing number of layers"
            )

        if analysis["large_layers"]:
            analysis["optimization_opportunities"].append(
                "Large layers detected - consider optimization"
            )

        if analysis["total_size"] > 1 * 1024 * 1024 * 1024:  # 1GB
            analysis["optimization_opportunities"].append(
                "Image size is large - consider multi-stage builds"
            )

        return analysis

    @staticmethod
    def calculate_image_size(image_info: dict[str, Any]) -> dict[str, Any]:
        """Calculate detailed image size information."""
        size_info = {
            "virtual_size": 0,
            "actual_size": 0,
            "shared_size": 0,
            "size_breakdown": {},
        }

        # Virtual size (what Docker reports)
        size_info["virtual_size"] = image_info.get("VirtualSize", 0)

        # Calculate actual size from layers
        layers = image_info.get("Layers", [])
        actual_size = sum(layer.get("Size", 0) for layer in layers)
        size_info["actual_size"] = actual_size

        # Shared size (difference between virtual and actual)
        size_info["shared_size"] = size_info["virtual_size"] - actual_size

        # Size breakdown
        size_info["size_breakdown"] = {
            "virtual_size_formatted": ImageUtils.format_image_size(
                size_info["virtual_size"]
            ),
            "actual_size_formatted": ImageUtils.format_image_size(actual_size),
            "shared_size_formatted": ImageUtils.format_image_size(
                size_info["shared_size"]
            ),
            "layer_count": len(layers),
            "average_layer_size": actual_size // len(layers) if layers else 0,
        }

        return size_info

    @staticmethod
    def format_image_size(size_bytes: int) -> str:
        """Format image size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    @staticmethod
    def analyze_image_security(image_info: dict[str, Any]) -> dict[str, Any]:
        """Analyze image for security considerations."""
        security_analysis = {
            "base_image": None,
            "user": None,
            "exposed_ports": [],
            "environment_variables": [],
            "security_issues": [],
            "recommendations": [],
        }

        config = image_info.get("Config", {})

        # Analyze base image
        from_line = config.get("Image", "")
        if from_line:
            security_analysis["base_image"] = from_line

        # Check user
        user = config.get("User", "")
        if user:
            security_analysis["user"] = user
            if user == "root" or user == "0":
                security_analysis["security_issues"].append("Image runs as root user")
                security_analysis["recommendations"].append("Use non-root user")

        # Check exposed ports
        exposed_ports = config.get("ExposedPorts", {})
        if exposed_ports:
            security_analysis["exposed_ports"] = list(exposed_ports.keys())
            if len(exposed_ports) > 5:
                security_analysis["security_issues"].append("Too many exposed ports")
                security_analysis["recommendations"].append("Minimize exposed ports")

        # Check environment variables
        env_vars = config.get("Env", [])
        security_analysis["environment_variables"] = env_vars

        # Check for sensitive environment variables
        sensitive_vars = ["PASSWORD", "SECRET", "KEY", "TOKEN", "CREDENTIAL"]
        for env_var in env_vars:
            if any(sensitive in env_var.upper() for sensitive in sensitive_vars):
                security_analysis["security_issues"].append(
                    f"Sensitive environment variable: {env_var}"
                )
                security_analysis["recommendations"].append(
                    "Use secrets management instead of environment variables"
                )

        return security_analysis

    @staticmethod
    def get_image_metadata(image_info: dict[str, Any]) -> dict[str, Any]:
        """Extract and format image metadata."""
        metadata = {
            "id": image_info.get("Id", ""),
            "tags": image_info.get("RepoTags", []),
            "digest": image_info.get("RepoDigests", []),
            "created": image_info.get("Created", ""),
            "architecture": image_info.get("Architecture", ""),
            "os": image_info.get("Os", ""),
            "author": image_info.get("Author", ""),
            "comment": image_info.get("Comment", ""),
            "labels": image_info.get("Config", {}).get("Labels", {}),
            "working_dir": image_info.get("Config", {}).get("WorkingDir", ""),
            "entrypoint": image_info.get("Config", {}).get("Entrypoint", []),
            "cmd": image_info.get("Config", {}).get("Cmd", []),
        }

        # Parse created timestamp
        if metadata["created"]:
            try:
                created_dt = datetime.fromisoformat(
                    metadata["created"].replace("Z", "+00:00")
                )
                metadata["created_formatted"] = created_dt.strftime(
                    "%Y-%m-%d %H:%M:%S UTC"
                )
                metadata["age_days"] = (
                    datetime.now(created_dt.tzinfo) - created_dt
                ).days
            except ValueError:
                metadata["created_formatted"] = metadata["created"]
                metadata["age_days"] = None

        return metadata

    @staticmethod
    def optimize_image_config(image_config: dict[str, Any]) -> dict[str, Any]:
        """Suggest optimizations for image configuration."""
        optimizations = {
            "size_optimizations": [],
            "security_optimizations": [],
            "performance_optimizations": [],
            "best_practices": [],
        }

        config = image_config.get("Config", {})

        # Size optimizations
        if config.get("User") == "root":
            optimizations["size_optimizations"].append(
                "Use non-root user to reduce attack surface"
            )

        # Security optimizations
        exposed_ports = config.get("ExposedPorts", {})
        if len(exposed_ports) > 3:
            optimizations["security_optimizations"].append("Minimize exposed ports")

        env_vars = config.get("Env", [])
        if len(env_vars) > 10:
            optimizations["security_optimizations"].append(
                "Consider reducing environment variables"
            )

        # Performance optimizations
        if not config.get("Healthcheck"):
            optimizations["performance_optimizations"].append(
                "Add health check for better monitoring"
            )

        # Best practices
        if not config.get("WorkingDir"):
            optimizations["best_practices"].append("Set working directory")

        if not config.get("Entrypoint"):
            optimizations["best_practices"].append(
                "Consider setting explicit entrypoint"
            )

        return optimizations

    @staticmethod
    def compare_images(
        image1_info: dict[str, Any], image2_info: dict[str, Any]
    ) -> dict[str, Any]:
        """Compare two Docker images."""
        comparison = {
            "size_difference": 0,
            "layer_difference": 0,
            "common_layers": 0,
            "unique_to_image1": 0,
            "unique_to_image2": 0,
            "similarity_percentage": 0.0,
        }

        # Size comparison
        size1 = image1_info.get("VirtualSize", 0)
        size2 = image2_info.get("VirtualSize", 0)
        comparison["size_difference"] = abs(size1 - size2)
        comparison["size_difference_formatted"] = ImageUtils.format_image_size(
            comparison["size_difference"]
        )

        # Layer comparison
        layers1 = set(layer.get("Id", "") for layer in image1_info.get("Layers", []))
        layers2 = set(layer.get("Id", "") for layer in image2_info.get("Layers", []))

        comparison["common_layers"] = len(layers1.intersection(layers2))
        comparison["unique_to_image1"] = len(layers1 - layers2)
        comparison["unique_to_image2"] = len(layers2 - layers1)
        comparison["layer_difference"] = (
            comparison["unique_to_image1"] + comparison["unique_to_image2"]
        )

        # Calculate similarity
        total_layers = len(layers1.union(layers2))
        if total_layers > 0:
            comparison["similarity_percentage"] = (
                comparison["common_layers"] / total_layers
            ) * 100

        return comparison
