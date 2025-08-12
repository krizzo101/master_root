"""
Volume Utilities

Volume-specific utility functions and helpers.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class VolumeUtils:
    """
    Volume utility functions.

    Provides volume-specific operations and helpers:
    - Volume analysis and optimization
    - Volume usage tracking
    - Volume management
    """

    @staticmethod
    def analyze_volume_config(volume_info: dict[str, Any]) -> dict[str, Any]:
        """Analyze Docker volume configuration."""
        analysis = {
            "volume_type": None,
            "driver_info": {},
            "mount_point": None,
            "usage_analysis": {},
            "recommendations": [],
        }

        # Analyze volume type
        driver = volume_info.get("Driver", "local")
        analysis["volume_type"] = driver

        # Analyze driver information
        analysis["driver_info"] = {
            "driver": driver,
            "driver_opts": volume_info.get("Options", {}),
            "scope": volume_info.get("Scope", "local"),
        }

        # Analyze mount point
        mount_point = volume_info.get("Mountpoint", "")
        analysis["mount_point"] = mount_point

        # Usage analysis
        usage_data = volume_info.get("UsageData", {})
        if usage_data:
            analysis["usage_analysis"] = {
                "size": usage_data.get("Size", 0),
                "size_formatted": VolumeUtils.format_volume_size(
                    usage_data.get("Size", 0)
                ),
                "ref_count": usage_data.get("RefCount", 0),
            }

        # Generate recommendations
        if (
            driver == "local"
            and usage_data
            and usage_data.get("Size", 0) > 10 * 1024 * 1024 * 1024
        ):  # 10GB
            analysis["recommendations"].append(
                "Consider using external storage for large volumes"
            )

        if not usage_data or usage_data.get("RefCount", 0) == 0:
            analysis["recommendations"].append(
                "Volume appears unused - consider cleanup"
            )

        return analysis

    @staticmethod
    def validate_volume_config(volume_config: dict[str, Any]) -> dict[str, Any]:
        """Validate volume configuration parameters."""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "driver_validation": {},
            "name_validation": {},
        }

        # Validate driver
        driver = volume_config.get("Driver", "local")
        valid_drivers = ["local", "nfs", "cifs", "tmpfs", "device", "overlay"]
        if driver not in valid_drivers:
            validation["errors"].append(f"Invalid driver: {driver}")
            validation["valid"] = False
        else:
            validation["driver_validation"] = {"driver": driver, "valid": True}

        # Validate name
        name = volume_config.get("Name", "")
        if name:
            if not name.replace("-", "").replace("_", "").isalnum():
                validation["warnings"].append("Volume name contains special characters")

            if len(name) > 64:
                validation["errors"].append("Volume name too long (max 64 characters)")
                validation["valid"] = False

            validation["name_validation"] = {"name": name, "valid": True}
        else:
            validation["warnings"].append("No volume name specified")

        # Validate driver options
        driver_opts = volume_config.get("DriverOpts", {})
        if driver == "nfs" and not driver_opts.get("share"):
            validation["errors"].append("NFS driver requires 'share' option")
            validation["valid"] = False

        if driver == "cifs" and not driver_opts.get("share"):
            validation["errors"].append("CIFS driver requires 'share' option")
            validation["valid"] = False

        return validation

    @staticmethod
    def get_volume_usage_stats(volume_info: dict[str, Any]) -> dict[str, Any]:
        """Get volume usage statistics."""
        stats = {
            "size_bytes": 0,
            "size_formatted": "0 B",
            "ref_count": 0,
            "last_used": None,
            "usage_percentage": 0.0,
        }

        usage_data = volume_info.get("UsageData", {})
        if usage_data:
            stats["size_bytes"] = usage_data.get("Size", 0)
            stats["size_formatted"] = VolumeUtils.format_volume_size(
                stats["size_bytes"]
            )
            stats["ref_count"] = usage_data.get("RefCount", 0)

        # Calculate usage percentage (rough estimate)
        # This would need actual filesystem information for accurate calculation
        if stats["size_bytes"] > 0:
            # Assume 100GB as typical volume size for percentage calculation
            typical_size = 100 * 1024 * 1024 * 1024  # 100GB
            stats["usage_percentage"] = min(
                (stats["size_bytes"] / typical_size) * 100, 100.0
            )

        return stats

    @staticmethod
    def format_volume_size(size_bytes: int) -> str:
        """Format volume size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    @staticmethod
    def troubleshoot_volume_issues(volume_info: dict[str, Any]) -> dict[str, Any]:
        """Troubleshoot volume-related issues."""
        troubleshooting = {"issues": [], "diagnostic_steps": [], "recommendations": []}

        # Check for common issues
        driver = volume_info.get("Driver", "")
        usage_data = volume_info.get("UsageData", {})

        # Check for unused volumes
        if not usage_data or usage_data.get("RefCount", 0) == 0:
            troubleshooting["issues"].append(
                "Volume is not being used by any containers"
            )
            troubleshooting["diagnostic_steps"].append(
                "Check if containers are properly mounting this volume"
            )
            troubleshooting["recommendations"].append("Consider removing unused volume")

        # Check for large volumes
        if usage_data and usage_data.get("Size", 0) > 50 * 1024 * 1024 * 1024:  # 50GB
            troubleshooting["issues"].append("Volume size is very large")
            troubleshooting["diagnostic_steps"].append(
                "Check for unnecessary files or logs"
            )
            troubleshooting["recommendations"].append(
                "Consider implementing log rotation and cleanup"
            )

        # Check for driver-specific issues
        if driver == "nfs":
            troubleshooting["diagnostic_steps"].append("Verify NFS server connectivity")
            troubleshooting["diagnostic_steps"].append("Check NFS mount permissions")

        if driver == "cifs":
            troubleshooting["diagnostic_steps"].append(
                "Verify CIFS server connectivity"
            )
            troubleshooting["diagnostic_steps"].append(
                "Check CIFS credentials and permissions"
            )

        return troubleshooting

    @staticmethod
    def optimize_volume_config(volume_config: dict[str, Any]) -> dict[str, Any]:
        """Suggest volume configuration optimizations."""
        optimizations = {
            "driver_optimizations": [],
            "performance_optimizations": [],
            "security_optimizations": [],
            "management_optimizations": [],
        }

        # Driver optimizations
        driver = volume_config.get("Driver", "local")
        if driver == "local":
            optimizations["driver_optimizations"].append(
                "Consider NFS for shared storage across hosts"
            )

        if driver == "nfs":
            optimizations["driver_optimizations"].append(
                "Consider CIFS for Windows compatibility"
            )

        # Performance optimizations
        driver_opts = volume_config.get("DriverOpts", {})
        if driver == "nfs" and not driver_opts.get("o"):
            optimizations["performance_optimizations"].append(
                "Add NFS mount options for better performance"
            )

        if driver == "local":
            optimizations["performance_optimizations"].append(
                "Consider using tmpfs for temporary data"
            )

        # Security optimizations
        if (
            driver in ["nfs", "cifs"]
            and not driver_opts.get("uid")
            and not driver_opts.get("gid")
        ):
            optimizations["security_optimizations"].append(
                "Set explicit UID/GID for better security"
            )

        # Management optimizations
        if not volume_config.get("Labels"):
            optimizations["management_optimizations"].append(
                "Add labels for better volume management"
            )

        return optimizations

    @staticmethod
    def format_volume_info(volume_info: dict[str, Any]) -> str:
        """Format volume information for display."""
        lines = []

        # Basic info
        lines.append(f"Volume: {volume_info.get('Name', 'Unknown')}")
        lines.append(f"Driver: {volume_info.get('Driver', 'Unknown')}")
        lines.append(f"Scope: {volume_info.get('Scope', 'Unknown')}")

        # Mount point
        mount_point = volume_info.get("Mountpoint", "")
        if mount_point:
            lines.append(f"Mount point: {mount_point}")

        # Usage info
        usage_data = volume_info.get("UsageData", {})
        if usage_data:
            size = usage_data.get("Size", 0)
            ref_count = usage_data.get("RefCount", 0)
            lines.append(f"Size: {VolumeUtils.format_volume_size(size)}")
            lines.append(f"Reference count: {ref_count}")

        return "\n".join(lines)

    @staticmethod
    def calculate_volume_space_usage(volume_info: dict[str, Any]) -> dict[str, Any]:
        """Calculate detailed volume space usage."""
        usage = {
            "total_space": 0,
            "used_space": 0,
            "available_space": 0,
            "usage_percentage": 0.0,
            "inode_usage": {},
            "file_count": 0,
        }

        # Get usage data
        usage_data = volume_info.get("UsageData", {})
        if usage_data:
            usage["used_space"] = usage_data.get("Size", 0)
            usage["used_space_formatted"] = VolumeUtils.format_volume_size(
                usage["used_space"]
            )

        # Note: For accurate total/available space, we would need filesystem information
        # This is a placeholder for when that information is available
        mount_point = volume_info.get("Mountpoint", "")
        if mount_point:
            usage["mount_point"] = mount_point
            # In a real implementation, we would use os.statvfs() here
            # to get actual filesystem statistics

        return usage
