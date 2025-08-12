"""
Network Utilities

Network-specific utility functions and helpers.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class NetworkUtils:
    """
    Network utility functions.

    Provides network-specific operations and helpers:
    - Network analysis and optimization
    - Network configuration validation
    - Network troubleshooting
    """

    @staticmethod
    def analyze_network_config(network_info: dict[str, Any]) -> dict[str, Any]:
        """Analyze Docker network configuration."""
        analysis = {
            "network_type": None,
            "subnet_info": {},
            "gateway_info": {},
            "ipam_config": {},
            "connectivity_analysis": {},
            "recommendations": [],
        }

        # Analyze network type
        driver = network_info.get("Driver", "bridge")
        analysis["network_type"] = driver

        # Analyze IPAM configuration
        ipam = network_info.get("IPAM", {})
        if ipam:
            config = ipam.get("Config", [])
            if config:
                subnet_config = config[0]
                analysis["subnet_info"] = {
                    "subnet": subnet_config.get("Subnet", ""),
                    "gateway": subnet_config.get("Gateway", ""),
                    "ip_range": subnet_config.get("IPRange", ""),
                }

        # Analyze gateway
        if analysis["subnet_info"].get("gateway"):
            analysis["gateway_info"] = {
                "gateway": analysis["subnet_info"]["gateway"],
                "gateway_valid": NetworkUtils._is_valid_ip(
                    analysis["subnet_info"]["gateway"]
                ),
            }

        # Connectivity analysis
        containers = network_info.get("Containers", {})
        analysis["connectivity_analysis"] = {
            "connected_containers": len(containers),
            "container_ips": list(containers.keys()),
            "network_utilization": (
                "low"
                if len(containers) < 5
                else "medium"
                if len(containers) < 20
                else "high"
            ),
        }

        # Generate recommendations
        if driver == "bridge" and len(containers) > 10:
            analysis["recommendations"].append(
                "Consider using overlay network for large container count"
            )

        if not analysis["subnet_info"].get("subnet"):
            analysis["recommendations"].append(
                "Consider specifying custom subnet for better control"
            )

        return analysis

    @staticmethod
    def validate_network_config(network_config: dict[str, Any]) -> dict[str, Any]:
        """Validate network configuration parameters."""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "subnet_validation": {},
            "driver_validation": {},
        }

        # Validate driver
        driver = network_config.get("Driver", "bridge")
        valid_drivers = ["bridge", "overlay", "host", "macvlan", "ipvlan", "none"]
        if driver not in valid_drivers:
            validation["errors"].append(f"Invalid driver: {driver}")
            validation["valid"] = False
        else:
            validation["driver_validation"] = {"driver": driver, "valid": True}

        # Validate subnet configuration
        ipam_config = network_config.get("IPAM", {}).get("Config", [])
        if ipam_config:
            subnet_config = ipam_config[0]
            subnet = subnet_config.get("Subnet", "")

            if subnet:
                validation["subnet_validation"] = {
                    "subnet": subnet,
                    "valid": NetworkUtils._is_valid_subnet(subnet),
                    "gateway": subnet_config.get("Gateway", ""),
                    "gateway_valid": NetworkUtils._is_valid_ip(
                        subnet_config.get("Gateway", "")
                    ),
                }

                if not validation["subnet_validation"]["valid"]:
                    validation["errors"].append(f"Invalid subnet: {subnet}")
                    validation["valid"] = False

                if (
                    subnet_config.get("Gateway")
                    and not validation["subnet_validation"]["gateway_valid"]
                ):
                    validation["errors"].append(
                        f"Invalid gateway: {subnet_config.get('Gateway')}"
                    )
                    validation["valid"] = False
            else:
                validation["warnings"].append("No subnet specified - using default")

        # Validate network name
        name = network_config.get("Name", "")
        if name and not name.replace("-", "").replace("_", "").isalnum():
            validation["warnings"].append("Network name contains special characters")

        return validation

    @staticmethod
    def _is_valid_subnet(subnet: str) -> bool:
        """Validate subnet CIDR notation."""
        try:
            if "/" not in subnet:
                return False

            ip_part, cidr_part = subnet.split("/")
            cidr = int(cidr_part)

            if not (0 <= cidr <= 32):
                return False

            # Basic IP validation
            parts = ip_part.split(".")
            if len(parts) != 4:
                return False

            for part in parts:
                if not (0 <= int(part) <= 255):
                    return False

            return True
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def _is_valid_ip(ip: str) -> bool:
        """Validate IP address format."""
        try:
            parts = ip.split(".")
            if len(parts) != 4:
                return False

            for part in parts:
                if not (0 <= int(part) <= 255):
                    return False

            return True
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def get_network_statistics(network_info: dict[str, Any]) -> dict[str, Any]:
        """Get network usage statistics."""
        stats = {
            "total_containers": 0,
            "active_containers": 0,
            "network_type": "",
            "subnet_usage": {},
            "bandwidth_usage": {},
        }

        # Container statistics
        containers = network_info.get("Containers", {})
        stats["total_containers"] = len(containers)
        stats["active_containers"] = len(
            [c for c in containers.values() if c.get("State", "") == "running"]
        )

        # Network type
        stats["network_type"] = network_info.get("Driver", "unknown")

        # Subnet usage analysis
        ipam_config = network_info.get("IPAM", {}).get("Config", [])
        if ipam_config:
            subnet_config = ipam_config[0]
            subnet = subnet_config.get("Subnet", "")
            if subnet and "/" in subnet:
                try:
                    cidr = int(subnet.split("/")[1])
                    total_ips = 2 ** (32 - cidr)
                    used_ips = len(containers)
                    available_ips = total_ips - used_ips

                    stats["subnet_usage"] = {
                        "subnet": subnet,
                        "total_ips": total_ips,
                        "used_ips": used_ips,
                        "available_ips": available_ips,
                        "usage_percentage": round((used_ips / total_ips) * 100, 2),
                    }
                except (ValueError, IndexError):
                    pass

        return stats

    @staticmethod
    def troubleshoot_network_connectivity(
        network_info: dict[str, Any]
    ) -> dict[str, Any]:
        """Troubleshoot network connectivity issues."""
        troubleshooting = {
            "connectivity_issues": [],
            "diagnostic_steps": [],
            "recommendations": [],
        }

        # Check for common issues
        containers = network_info.get("Containers", {})

        if not containers:
            troubleshooting["connectivity_issues"].append(
                "No containers connected to network"
            )
            troubleshooting["diagnostic_steps"].append(
                "Check if containers are running and connected"
            )

        # Check for IP conflicts
        container_ips = []
        for container in containers.values():
            ip = container.get("IPv4Address", "")
            if ip and ip in container_ips:
                troubleshooting["connectivity_issues"].append(
                    f"IP conflict detected: {ip}"
                )
            container_ips.append(ip)

        # Check network driver
        driver = network_info.get("Driver", "")
        if driver == "host":
            troubleshooting["recommendations"].append(
                "Host network mode may cause port conflicts"
            )

        # Check subnet configuration
        ipam_config = network_info.get("IPAM", {}).get("Config", [])
        if ipam_config:
            subnet_config = ipam_config[0]
            if not subnet_config.get("Subnet"):
                troubleshooting["connectivity_issues"].append("No subnet configured")
                troubleshooting["diagnostic_steps"].append(
                    "Configure subnet for network"
                )

        return troubleshooting

    @staticmethod
    def optimize_network_config(network_config: dict[str, Any]) -> dict[str, Any]:
        """Suggest network configuration optimizations."""
        optimizations = {
            "driver_optimizations": [],
            "subnet_optimizations": [],
            "security_optimizations": [],
            "performance_optimizations": [],
        }

        # Driver optimizations
        driver = network_config.get("Driver", "bridge")
        if driver == "bridge":
            optimizations["driver_optimizations"].append(
                "Consider overlay driver for multi-host deployments"
            )

        # Subnet optimizations
        ipam_config = network_config.get("IPAM", {}).get("Config", [])
        if ipam_config:
            subnet_config = ipam_config[0]
            subnet = subnet_config.get("Subnet", "")

            if subnet and "/" in subnet:
                cidr = int(subnet.split("/")[1])
                if cidr > 24:  # Small subnet
                    optimizations["subnet_optimizations"].append(
                        "Consider larger subnet for scalability"
                    )
                elif cidr < 16:  # Large subnet
                    optimizations["subnet_optimizations"].append(
                        "Consider smaller subnet to conserve IP space"
                    )

        # Security optimizations
        if not network_config.get("Internal", False):
            optimizations["security_optimizations"].append(
                "Consider internal network for sensitive containers"
            )

        # Performance optimizations
        if driver == "bridge":
            optimizations["performance_optimizations"].append(
                "Consider macvlan for better performance"
            )

        return optimizations

    @staticmethod
    def format_network_info(network_info: dict[str, Any]) -> str:
        """Format network information for display."""
        lines = []

        # Basic info
        lines.append(f"Network: {network_info.get('Name', 'Unknown')}")
        lines.append(f"Driver: {network_info.get('Driver', 'Unknown')}")
        lines.append(f"Scope: {network_info.get('Scope', 'Unknown')}")

        # IPAM info
        ipam = network_info.get("IPAM", {})
        if ipam:
            config = ipam.get("Config", [])
            if config:
                subnet_config = config[0]
                lines.append(f"Subnet: {subnet_config.get('Subnet', 'Not specified')}")
                lines.append(
                    f"Gateway: {subnet_config.get('Gateway', 'Not specified')}"
                )

        # Container count
        containers = network_info.get("Containers", {})
        lines.append(f"Connected containers: {len(containers)}")

        return "\n".join(lines)
