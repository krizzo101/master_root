"""
Container Utilities

Container-specific utility functions and helpers.
"""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class ContainerUtils:
    """
    Container utility functions.

    Provides container-specific operations and helpers:
    - Container lifecycle management
    - Container inspection and analysis
    - Container optimization
    """

    @staticmethod
    def analyze_container_config(container_config: dict[str, Any]) -> dict[str, Any]:
        """Analyze container configuration for best practices and issues."""
        analysis = {
            "issues": [],
            "warnings": [],
            "recommendations": [],
            "security_score": 100,
        }

        # Check for root user
        if (
            container_config.get("User") == "root"
            or container_config.get("User") == "0"
        ):
            analysis["warnings"].append("Container runs as root user")
            analysis["security_score"] -= 20

        # Check for privileged mode
        if container_config.get("HostConfig", {}).get("Privileged", False):
            analysis["issues"].append("Container runs in privileged mode")
            analysis["security_score"] -= 30

        # Check for exposed ports
        exposed_ports = container_config.get("Config", {}).get("ExposedPorts", {})
        if len(exposed_ports) > 5:
            analysis["warnings"].append(f"Container exposes {len(exposed_ports)} ports")
            analysis["security_score"] -= 10

        # Check for resource limits
        host_config = container_config.get("HostConfig", {})
        if not host_config.get("Memory"):
            analysis["recommendations"].append("Consider setting memory limits")
        if not host_config.get("CpuShares"):
            analysis["recommendations"].append("Consider setting CPU limits")

        # Check for health check
        if not container_config.get("Config", {}).get("Healthcheck"):
            analysis["recommendations"].append("Consider adding health check")

        # Check for read-only root filesystem
        if not host_config.get("ReadonlyRootfs", False):
            analysis["recommendations"].append(
                "Consider using read-only root filesystem"
            )

        return analysis

    @staticmethod
    def get_container_usage_stats(container_stats: dict[str, Any]) -> dict[str, Any]:
        """Extract and format container usage statistics."""
        try:
            cpu_stats = container_stats.get("cpu_stats", {})
            memory_stats = container_stats.get("memory_stats", {})
            network_stats = container_stats.get("networks", {})

            # Calculate CPU usage
            cpu_usage = 0.0
            if cpu_stats:
                cpu_delta = cpu_stats.get("cpu_usage", {}).get("total_usage", 0)
                system_delta = cpu_stats.get("system_cpu_usage", 0)
                if system_delta > 0:
                    cpu_usage = (cpu_delta / system_delta) * 100.0

            # Calculate memory usage
            memory_usage = 0.0
            memory_limit = 0
            if memory_stats:
                memory_usage = memory_stats.get("usage", 0)
                memory_limit = memory_stats.get("limit", 0)

            # Calculate network usage
            network_rx = 0
            network_tx = 0
            if network_stats:
                for interface in network_stats.values():
                    network_rx += interface.get("rx_bytes", 0)
                    network_tx += interface.get("tx_bytes", 0)

            return {
                "cpu_usage_percent": round(cpu_usage, 2),
                "memory_usage_bytes": memory_usage,
                "memory_limit_bytes": memory_limit,
                "memory_usage_percent": (
                    round((memory_usage / memory_limit) * 100, 2)
                    if memory_limit > 0
                    else 0
                ),
                "network_rx_bytes": network_rx,
                "network_tx_bytes": network_tx,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error processing container stats: {e}")
            return {"error": str(e)}

    @staticmethod
    def format_container_logs(logs: str, max_lines: int = 100) -> str:
        """Format container logs for better readability."""
        if not logs:
            return ""

        lines = logs.strip().split("\n")

        # Truncate if too many lines
        if len(lines) > max_lines:
            lines = lines[-max_lines:]
            lines.insert(0, f"... (showing last {max_lines} lines)")

        # Add line numbers and timestamps if available
        formatted_lines = []
        for i, line in enumerate(lines, 1):
            if line.startswith("..."):
                formatted_lines.append(line)
            else:
                # Try to extract timestamp if present
                if " " in line and len(line) > 20:
                    timestamp_part = line[:20]
                    try:
                        datetime.fromisoformat(timestamp_part.replace("Z", "+00:00"))
                        formatted_lines.append(f"[{i:3d}] {line}")
                    except ValueError:
                        formatted_lines.append(f"[{i:3d}] {line}")
                else:
                    formatted_lines.append(f"[{i:3d}] {line}")

        return "\n".join(formatted_lines)

    @staticmethod
    def parse_container_ports(port_bindings: dict[str, Any]) -> list[dict[str, str]]:
        """Parse container port bindings into a structured format."""
        ports = []

        for container_port, host_bindings in port_bindings.items():
            if host_bindings:
                for binding in host_bindings:
                    ports.append(
                        {
                            "container_port": container_port,
                            "host_ip": binding.get("HostIp", "0.0.0.0"),
                            "host_port": binding.get("HostPort", ""),
                        }
                    )
            else:
                ports.append(
                    {
                        "container_port": container_port,
                        "host_ip": "0.0.0.0",
                        "host_port": "",
                    }
                )

        return ports

    @staticmethod
    def get_container_environment_variables(
        container_config: dict[str, Any]
    ) -> dict[str, str]:
        """Extract environment variables from container configuration."""
        env_vars = {}

        config = container_config.get("Config", {})
        env_list = config.get("Env", [])

        for env_var in env_list:
            if "=" in env_var:
                key, value = env_var.split("=", 1)
                env_vars[key] = value

        return env_vars

    @staticmethod
    def check_container_security(container_config: dict[str, Any]) -> dict[str, Any]:
        """Perform security analysis of container configuration."""
        security_analysis = {
            "score": 100,
            "issues": [],
            "warnings": [],
            "recommendations": [],
        }

        host_config = container_config.get("HostConfig", {})
        config = container_config.get("Config", {})

        # Check privileged mode
        if host_config.get("Privileged", False):
            security_analysis["issues"].append("Container runs in privileged mode")
            security_analysis["score"] -= 30

        # Check user
        user = config.get("User", "")
        if user == "root" or user == "0":
            security_analysis["warnings"].append("Container runs as root user")
            security_analysis["score"] -= 20

        # Check read-only root filesystem
        if not host_config.get("ReadonlyRootfs", False):
            security_analysis["recommendations"].append("Use read-only root filesystem")
            security_analysis["score"] -= 10

        # Check security options
        security_opts = host_config.get("SecurityOpt", [])
        if not any("no-new-privileges" in opt for opt in security_opts):
            security_analysis["recommendations"].append(
                "Add no-new-privileges security option"
            )
            security_analysis["score"] -= 10

        # Check capabilities
        cap_add = host_config.get("CapAdd", [])
        cap_drop = host_config.get("CapDrop", [])
        if cap_add and not cap_drop:
            security_analysis["warnings"].append(
                "Capabilities added without dropping unnecessary ones"
            )
            security_analysis["score"] -= 15

        # Check network mode
        network_mode = host_config.get("NetworkMode", "default")
        if network_mode == "host":
            security_analysis["issues"].append("Container uses host network mode")
            security_analysis["score"] -= 25

        # Ensure score doesn't go below 0
        security_analysis["score"] = max(0, security_analysis["score"])

        return security_analysis

    @staticmethod
    def optimize_container_config(container_config: dict[str, Any]) -> dict[str, Any]:
        """Suggest optimizations for container configuration."""
        optimizations = {
            "memory_optimizations": [],
            "cpu_optimizations": [],
            "security_optimizations": [],
            "performance_optimizations": [],
        }

        host_config = container_config.get("HostConfig", {})
        config = container_config.get("Config", {})

        # Memory optimizations
        if not host_config.get("Memory"):
            optimizations["memory_optimizations"].append(
                "Set memory limit to prevent OOM"
            )

        if not host_config.get("MemorySwap"):
            optimizations["memory_optimizations"].append("Set memory swap limit")

        # CPU optimizations
        if not host_config.get("CpuShares"):
            optimizations["cpu_optimizations"].append(
                "Set CPU shares for fair scheduling"
            )

        if not host_config.get("CpuPeriod"):
            optimizations["cpu_optimizations"].append(
                "Set CPU period for better control"
            )

        # Security optimizations
        if not host_config.get("ReadonlyRootfs", False):
            optimizations["security_optimizations"].append(
                "Enable read-only root filesystem"
            )

        if config.get("User") == "root":
            optimizations["security_optimizations"].append("Run as non-root user")

        # Performance optimizations
        if not config.get("Healthcheck"):
            optimizations["performance_optimizations"].append(
                "Add health check for better monitoring"
            )

        if not host_config.get("RestartPolicy"):
            optimizations["performance_optimizations"].append(
                "Set restart policy for reliability"
            )

        return optimizations
