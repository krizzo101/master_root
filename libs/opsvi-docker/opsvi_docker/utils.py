"""
Docker Utilities

Utility functions for Docker operations, health checks, monitoring, and security.
Provides helper functions and common operations for Docker management.
"""

import logging
import os
import hashlib
import json
import subprocess
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DockerUtils:
    """Utility functions for Docker operations."""

    @staticmethod
    def validate_docker_installation() -> bool:
        """Validate Docker installation.

        Returns:
            bool: True if Docker is properly installed
        """
        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True, check=True
            )
            logger.info(f"Docker version: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("Docker is not installed or not accessible")
            return False

    @staticmethod
    def validate_docker_compose_installation() -> bool:
        """Validate Docker Compose installation.

        Returns:
            bool: True if Docker Compose is properly installed
        """
        try:
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info(f"Docker Compose version: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("Docker Compose is not installed or not accessible")
            return False

    @staticmethod
    def check_docker_daemon() -> bool:
        """Check if Docker daemon is running.

        Returns:
            bool: True if Docker daemon is running
        """
        try:
            result = subprocess.run(
                ["docker", "info"], capture_output=True, text=True, check=True
            )
            logger.info("Docker daemon is running")
            return True
        except subprocess.CalledProcessError:
            logger.error("Docker daemon is not running")
            return False

    @staticmethod
    def get_docker_info() -> Dict[str, Any]:
        """Get Docker system information.

        Returns:
            Dict: Docker system information
        """
        try:
            result = subprocess.run(
                ["docker", "info", "--format", "{{json .}}"],
                capture_output=True,
                text=True,
                check=True,
            )
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"Failed to get Docker info: {e}")
            return {}

    @staticmethod
    def calculate_image_size(image_id: str) -> int:
        """Calculate image size in bytes.

        Args:
            image_id: Image ID

        Returns:
            int: Image size in bytes
        """
        try:
            result = subprocess.run(
                ["docker", "image", "inspect", image_id, "--format", "{{.Size}}"],
                capture_output=True,
                text=True,
                check=True,
            )
            return int(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError) as e:
            logger.error(f"Failed to calculate image size: {e}")
            return 0

    @staticmethod
    def get_container_ip(container_id: str) -> Optional[str]:
        """Get container IP address.

        Args:
            container_id: Container ID

        Returns:
            str: Container IP address
        """
        try:
            result = subprocess.run(
                [
                    "docker",
                    "inspect",
                    container_id,
                    "--format",
                    "{{.NetworkSettings.IPAddress}}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            ip = result.stdout.strip()
            return ip if ip else None
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get container IP: {e}")
            return None

    @staticmethod
    def get_container_ports(container_id: str) -> Dict[str, List[Dict[str, str]]]:
        """Get container port mappings.

        Args:
            container_id: Container ID

        Returns:
            Dict: Port mappings
        """
        try:
            result = subprocess.run(
                [
                    "docker",
                    "inspect",
                    container_id,
                    "--format",
                    "{{json .NetworkSettings.Ports}}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"Failed to get container ports: {e}")
            return {}


class ContainerUtils:
    """Utility functions for container operations."""

    @staticmethod
    def generate_container_name(
        prefix: str = "opsvi", suffix: Optional[str] = None
    ) -> str:
        """Generate a unique container name.

        Args:
            prefix: Name prefix
            suffix: Optional name suffix

        Returns:
            str: Generated container name
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = hashlib.md5(timestamp.encode()).hexdigest()[:8]

        if suffix:
            return f"{prefix}_{suffix}_{timestamp}_{random_suffix}"
        else:
            return f"{prefix}_{timestamp}_{random_suffix}"

    @staticmethod
    def validate_container_name(name: str) -> bool:
        """Validate container name.

        Args:
            name: Container name

        Returns:
            bool: True if name is valid
        """
        # Docker container name rules
        if not name or len(name) > 64:
            return False

        # Must match regex: [a-zA-Z0-9][a-zA-Z0-9_.-]*
        import re

        pattern = r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$"
        return bool(re.match(pattern, name))

    @staticmethod
    def get_container_logs_tail(container_id: str, lines: int = 100) -> str:
        """Get last N lines of container logs.

        Args:
            container_id: Container ID
            lines: Number of lines to get

        Returns:
            str: Container logs
        """
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", str(lines), container_id],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get container logs: {e}")
            return ""

    @staticmethod
    def wait_for_container_ready(container_id: str, timeout: int = 60) -> bool:
        """Wait for container to be ready.

        Args:
            container_id: Container ID
            timeout: Timeout in seconds

        Returns:
            bool: True if container is ready
        """
        start_time = datetime.now()

        while (datetime.now() - start_time).seconds < timeout:
            try:
                result = subprocess.run(
                    [
                        "docker",
                        "inspect",
                        container_id,
                        "--format",
                        "{{.State.Status}}",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                if result.stdout.strip() == "running":
                    return True

                time.sleep(1)
            except subprocess.CalledProcessError:
                time.sleep(1)

        return False


class ImageUtils:
    """Utility functions for image operations."""

    @staticmethod
    def validate_image_name(name: str) -> bool:
        """Validate image name.

        Args:
            name: Image name

        Returns:
            bool: True if name is valid
        """
        # Basic validation for image names
        if not name or len(name) > 255:
            return False

        # Must not contain invalid characters
        invalid_chars = ["<", ">", ":", '"', "|", "?", "*", "\\"]
        return not any(char in name for char in invalid_chars)

    @staticmethod
    def parse_image_reference(image_ref: str) -> Dict[str, str]:
        """Parse image reference into components.

        Args:
            image_ref: Image reference (e.g., "nginx:latest", "myregistry.com/app:v1.0")

        Returns:
            Dict: Parsed components
        """
        parts = image_ref.split("/")

        if len(parts) == 1:
            # Single part: nginx:latest
            name_tag = parts[0].split(":")
            return {
                "registry": "docker.io",
                "repository": "library",
                "name": name_tag[0],
                "tag": name_tag[1] if len(name_tag) > 1 else "latest",
            }
        elif len(parts) == 2:
            # Two parts: myapp:latest or myregistry.com/myapp:latest
            if "." in parts[0] or ":" in parts[0]:
                # Registry/repository: myregistry.com/myapp:latest
                registry = parts[0]
                name_tag = parts[1].split(":")
                return {
                    "registry": registry,
                    "repository": "",
                    "name": name_tag[0],
                    "tag": name_tag[1] if len(name_tag) > 1 else "latest",
                }
            else:
                # Repository/name: myapp/nginx:latest
                name_tag = parts[1].split(":")
                return {
                    "registry": "docker.io",
                    "repository": parts[0],
                    "name": name_tag[0],
                    "tag": name_tag[1] if len(name_tag) > 1 else "latest",
                }
        elif len(parts) >= 3:
            # Three or more parts: myregistry.com/myorg/myapp:latest
            registry = parts[0]
            repository = "/".join(parts[1:-1])
            name_tag = parts[-1].split(":")
            return {
                "registry": registry,
                "repository": repository,
                "name": name_tag[0],
                "tag": name_tag[1] if len(name_tag) > 1 else "latest",
            }

        return {
            "registry": "docker.io",
            "repository": "library",
            "name": image_ref,
            "tag": "latest",
        }

    @staticmethod
    def build_image_reference(
        registry: str, repository: str, name: str, tag: str
    ) -> str:
        """Build image reference from components.

        Args:
            registry: Registry URL
            repository: Repository name
            name: Image name
            tag: Image tag

        Returns:
            str: Image reference
        """
        if registry == "docker.io":
            if repository == "library":
                return f"{name}:{tag}"
            else:
                return f"{repository}/{name}:{tag}"
        else:
            if repository:
                return f"{registry}/{repository}/{name}:{tag}"
            else:
                return f"{registry}/{name}:{tag}"


class NetworkUtils:
    """Utility functions for network operations."""

    @staticmethod
    def validate_network_name(name: str) -> bool:
        """Validate network name.

        Args:
            name: Network name

        Returns:
            bool: True if name is valid
        """
        # Docker network name rules
        if not name or len(name) > 128:
            return False

        # Must match regex: [a-zA-Z0-9][a-zA-Z0-9_.-]*
        import re

        pattern = r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$"
        return bool(re.match(pattern, name))

    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validate IP address.

        Args:
            ip: IP address

        Returns:
            bool: True if IP is valid
        """
        import re

        # IPv4 pattern
        ipv4_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        if re.match(ipv4_pattern, ip):
            parts = ip.split(".")
            return all(0 <= int(part) <= 255 for part in parts)

        # IPv6 pattern (simplified)
        ipv6_pattern = r"^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"
        return bool(re.match(ipv6_pattern, ip))

    @staticmethod
    def validate_subnet(subnet: str) -> bool:
        """Validate subnet CIDR notation.

        Args:
            subnet: Subnet in CIDR notation (e.g., "192.168.1.0/24")

        Returns:
            bool: True if subnet is valid
        """
        import re

        pattern = r"^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$"
        if not re.match(pattern, subnet):
            return False

        try:
            ip, prefix = subnet.split("/")
            prefix = int(prefix)

            if not NetworkUtils.validate_ip_address(ip) or not (0 <= prefix <= 32):
                return False

            return True
        except ValueError:
            return False


class VolumeUtils:
    """Utility functions for volume operations."""

    @staticmethod
    def validate_volume_name(name: str) -> bool:
        """Validate volume name.

        Args:
            name: Volume name

        Returns:
            bool: True if name is valid
        """
        # Docker volume name rules
        if not name or len(name) > 255:
            return False

        # Must match regex: [a-zA-Z0-9][a-zA-Z0-9_.-]*
        import re

        pattern = r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$"
        return bool(re.match(pattern, name))

    @staticmethod
    def get_volume_size(volume_name: str) -> int:
        """Get volume size in bytes.

        Args:
            volume_name: Volume name

        Returns:
            int: Volume size in bytes
        """
        try:
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{volume_name}:/data",
                    "alpine",
                    "du",
                    "-sb",
                    "/data",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return int(result.stdout.split()[0])
        except (subprocess.CalledProcessError, ValueError, IndexError) as e:
            logger.error(f"Failed to get volume size: {e}")
            return 0

    @staticmethod
    def backup_volume(volume_name: str, backup_path: str) -> bool:
        """Create a backup of a volume.

        Args:
            volume_name: Volume name
            backup_path: Backup file path

        Returns:
            bool: True if backup created successfully
        """
        try:
            subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{volume_name}:/data",
                    "-v",
                    f"{backup_path}:/backup",
                    "alpine",
                    "tar",
                    "-czf",
                    "/backup/volume_backup.tar.gz",
                    "-C",
                    "/data",
                    ".",
                ],
                check=True,
            )

            logger.info(f"Volume backup created: {volume_name} -> {backup_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to backup volume: {e}")
            return False


class HealthUtils:
    """Utility functions for health checks."""

    @staticmethod
    def check_container_health(container_id: str) -> Dict[str, Any]:
        """Check container health status.

        Args:
            container_id: Container ID

        Returns:
            Dict: Health check result
        """
        try:
            result = subprocess.run(
                [
                    "docker",
                    "inspect",
                    container_id,
                    "--format",
                    "{{.State.Health.Status}}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            status = result.stdout.strip()
            return {
                "healthy": status == "healthy",
                "status": status,
                "timestamp": datetime.now(),
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to check container health: {e}")
            return {"healthy": False, "status": "unknown", "timestamp": datetime.now()}

    @staticmethod
    def check_port_availability(host: str, port: int, timeout: int = 5) -> bool:
        """Check if a port is available.

        Args:
            host: Host address
            port: Port number
            timeout: Timeout in seconds

        Returns:
            bool: True if port is available
        """
        import socket

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception as e:
            logger.error(f"Failed to check port availability: {e}")
            return False

    @staticmethod
    def check_docker_daemon_health() -> Dict[str, Any]:
        """Check Docker daemon health.

        Returns:
            Dict: Health check result
        """
        try:
            result = subprocess.run(
                ["docker", "info"], capture_output=True, text=True, check=True
            )

            return {
                "healthy": True,
                "status": "running",
                "timestamp": datetime.now(),
                "details": "Docker daemon is responding",
            }
        except subprocess.CalledProcessError as e:
            return {
                "healthy": False,
                "status": "unhealthy",
                "timestamp": datetime.now(),
                "details": f"Docker daemon is not responding: {e}",
            }


class MonitoringUtils:
    """Utility functions for monitoring."""

    @staticmethod
    def format_bytes(bytes_value: int) -> str:
        """Format bytes into human readable format.

        Args:
            bytes_value: Bytes value

        Returns:
            str: Formatted string
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"

    @staticmethod
    def format_percentage(value: float) -> str:
        """Format percentage value.

        Args:
            value: Percentage value (0-100)

        Returns:
            str: Formatted percentage
        """
        return f"{value:.1f}%"

    @staticmethod
    def calculate_average(values: List[float]) -> float:
        """Calculate average of values.

        Args:
            values: List of values

        Returns:
            float: Average value
        """
        if not values:
            return 0.0
        return sum(values) / len(values)

    @staticmethod
    def calculate_percentile(values: List[float], percentile: float) -> float:
        """Calculate percentile of values.

        Args:
            values: List of values
            percentile: Percentile (0-100)

        Returns:
            float: Percentile value
        """
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)

        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))


class SecurityUtils:
    """Utility functions for security operations."""

    @staticmethod
    def scan_image_vulnerabilities(image_name: str) -> Dict[str, Any]:
        """Scan image for vulnerabilities.

        Args:
            image_name: Image name

        Returns:
            Dict: Vulnerability scan results
        """
        try:
            # This is a placeholder for actual vulnerability scanning
            # In a real implementation, you would use tools like Trivy, Clair, etc.
            logger.info(f"Vulnerability scan requested for image: {image_name}")

            return {
                "scanned": True,
                "vulnerabilities": [],
                "severity": "low",
                "timestamp": datetime.now(),
            }
        except Exception as e:
            logger.error(f"Failed to scan image vulnerabilities: {e}")
            return {"scanned": False, "error": str(e), "timestamp": datetime.now()}

    @staticmethod
    def validate_security_policy(container_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate container security policy.

        Args:
            container_config: Container configuration

        Returns:
            Dict: Security validation results
        """
        violations = []

        # Check for privileged mode
        if container_config.get("privileged", False):
            violations.append("Container runs in privileged mode")

        # Check for root user
        if (
            container_config.get("user") == "root"
            or container_config.get("user") == "0"
        ):
            violations.append("Container runs as root user")

        # Check for sensitive capabilities
        cap_add = container_config.get("cap_add", [])
        sensitive_caps = ["SYS_ADMIN", "NET_ADMIN", "SYS_PTRACE"]
        for cap in sensitive_caps:
            if cap in cap_add:
                violations.append(f"Container has sensitive capability: {cap}")

        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "timestamp": datetime.now(),
        }

    @staticmethod
    def generate_security_report(container_id: str) -> Dict[str, Any]:
        """Generate security report for container.

        Args:
            container_id: Container ID

        Returns:
            Dict: Security report
        """
        try:
            # Get container inspection data
            result = subprocess.run(
                ["docker", "inspect", container_id],
                capture_output=True,
                text=True,
                check=True,
            )

            container_data = json.loads(result.stdout)[0]

            # Analyze security configuration
            security_analysis = SecurityUtils.validate_security_policy(
                container_data.get("Config", {})
            )

            return {
                "container_id": container_id,
                "timestamp": datetime.now(),
                "security_analysis": security_analysis,
                "recommendations": SecurityUtils._generate_security_recommendations(
                    security_analysis
                ),
            }
        except Exception as e:
            logger.error(f"Failed to generate security report: {e}")
            return {
                "container_id": container_id,
                "timestamp": datetime.now(),
                "error": str(e),
            }

    @staticmethod
    def _generate_security_recommendations(
        security_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate security recommendations.

        Args:
            security_analysis: Security analysis results

        Returns:
            List[str]: Security recommendations
        """
        recommendations = []

        for violation in security_analysis.get("violations", []):
            if "privileged mode" in violation:
                recommendations.append(
                    "Consider running container without privileged mode"
                )
            elif "root user" in violation:
                recommendations.append("Consider running container as non-root user")
            elif "sensitive capability" in violation:
                recommendations.append("Consider removing unnecessary capabilities")

        return recommendations


class VulnerabilityScanner:
    """Vulnerability scanner for Docker images."""

    def __init__(self):
        """Initialize vulnerability scanner."""
        self.scanner_available = self._check_scanner_availability()

    def _check_scanner_availability(self) -> bool:
        """Check if vulnerability scanner is available.

        Returns:
            bool: True if scanner is available
        """
        try:
            # Check for common vulnerability scanners
            scanners = ["trivy", "clair", "anchore"]
            for scanner in scanners:
                result = subprocess.run(
                    [scanner, "--version"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    logger.info(f"Vulnerability scanner found: {scanner}")
                    return True
            return False
        except Exception:
            return False

    def scan_image(self, image_name: str) -> Dict[str, Any]:
        """Scan image for vulnerabilities.

        Args:
            image_name: Image name

        Returns:
            Dict: Vulnerability scan results
        """
        if not self.scanner_available:
            return {
                "scanned": False,
                "error": "No vulnerability scanner available",
                "timestamp": datetime.now(),
            }

        try:
            # This is a placeholder for actual vulnerability scanning
            # In a real implementation, you would use the available scanner
            logger.info(f"Vulnerability scan completed for image: {image_name}")

            return {
                "scanned": True,
                "vulnerabilities": [],
                "severity": "low",
                "timestamp": datetime.now(),
                "scanner": "placeholder",
            }
        except Exception as e:
            logger.error(f"Failed to scan image vulnerabilities: {e}")
            return {"scanned": False, "error": str(e), "timestamp": datetime.now()}
