"""
Health Utility Functions

Docker health checking and monitoring utilities.
Provides health assessment and diagnostic capabilities.
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Health check result data."""

    component: str
    status: str  # healthy, unhealthy, unknown
    message: str
    timestamp: datetime
    duration_ms: float
    details: dict[str, Any]


class HealthUtils:
    """
    Health utility functions.

    Provides health checking and monitoring utilities:
    - Container health assessment
    - Service availability checks
    - Performance monitoring
    - Alert generation
    """

    @staticmethod
    def check_container_health(
        container_info: dict[str, Any], timeout: int = 30
    ) -> HealthCheckResult:
        """Check container health status."""
        start_time = time.time()

        try:
            state = container_info.get("State", {})
            health = state.get("Health", {})

            # Check if container is running
            if not state.get("Running", False):
                return HealthCheckResult(
                    component="container",
                    status="unhealthy",
                    message="Container is not running",
                    timestamp=datetime.now(),
                    duration_ms=(time.time() - start_time) * 1000,
                    details={
                        "container_id": container_info.get("Id", "")[:12],
                        "status": state.get("Status", "unknown"),
                        "exit_code": state.get("ExitCode"),
                        "error": state.get("Error", ""),
                    },
                )

            # Check health status if available
            if health:
                health_status = health.get("Status", "unknown")
                failing_streak = health.get("FailingStreak", 0)

                status = "healthy" if health_status == "healthy" else "unhealthy"
                message = f"Health status: {health_status}"

                if failing_streak > 0:
                    message += f" (failing streak: {failing_streak})"

                return HealthCheckResult(
                    component="container",
                    status=status,
                    message=message,
                    timestamp=datetime.now(),
                    duration_ms=(time.time() - start_time) * 1000,
                    details={
                        "container_id": container_info.get("Id", "")[:12],
                        "health_status": health_status,
                        "failing_streak": failing_streak,
                        "log": health.get("Log", []),
                    },
                )

            # No explicit health check, assume healthy if running
            return HealthCheckResult(
                component="container",
                status="healthy",
                message="Container is running (no health check configured)",
                timestamp=datetime.now(),
                duration_ms=(time.time() - start_time) * 1000,
                details={
                    "container_id": container_info.get("Id", "")[:12],
                    "uptime": HealthUtils._calculate_uptime(state.get("StartedAt", "")),
                },
            )

        except Exception as e:
            return HealthCheckResult(
                component="container",
                status="unknown",
                message=f"Health check failed: {str(e)}",
                timestamp=datetime.now(),
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
            )

    @staticmethod
    def check_service_availability(
        host: str, port: int, timeout: int = 5
    ) -> HealthCheckResult:
        """Check if a service is available on host:port."""
        start_time = time.time()

        try:
            import socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                return HealthCheckResult(
                    component="service",
                    status="healthy",
                    message=f"Service available at {host}:{port}",
                    timestamp=datetime.now(),
                    duration_ms=(time.time() - start_time) * 1000,
                    details={"host": host, "port": port},
                )
            else:
                return HealthCheckResult(
                    component="service",
                    status="unhealthy",
                    message=f"Service unavailable at {host}:{port}",
                    timestamp=datetime.now(),
                    duration_ms=(time.time() - start_time) * 1000,
                    details={"host": host, "port": port, "error_code": result},
                )

        except Exception as e:
            return HealthCheckResult(
                component="service",
                status="unknown",
                message=f"Service check failed: {str(e)}",
                timestamp=datetime.now(),
                duration_ms=(time.time() - start_time) * 1000,
                details={"host": host, "port": port, "error": str(e)},
            )

    @staticmethod
    def check_docker_daemon() -> HealthCheckResult:
        """Check Docker daemon health."""
        start_time = time.time()

        try:
            import subprocess

            result = subprocess.run(
                ["docker", "info"], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                # Parse some basic info
                info_lines = result.stdout.split("\n")
                containers_running = 0
                containers_total = 0

                for line in info_lines:
                    if "Containers:" in line:
                        containers_total = int(line.split(":")[1].strip())
                    elif "Running:" in line:
                        containers_running = int(line.split(":")[1].strip())

                return HealthCheckResult(
                    component="docker_daemon",
                    status="healthy",
                    message="Docker daemon is running",
                    timestamp=datetime.now(),
                    duration_ms=(time.time() - start_time) * 1000,
                    details={
                        "containers_total": containers_total,
                        "containers_running": containers_running,
                    },
                )
            else:
                return HealthCheckResult(
                    component="docker_daemon",
                    status="unhealthy",
                    message=f"Docker daemon check failed: {result.stderr}",
                    timestamp=datetime.now(),
                    duration_ms=(time.time() - start_time) * 1000,
                    details={"error": result.stderr},
                )

        except Exception as e:
            return HealthCheckResult(
                component="docker_daemon",
                status="unknown",
                message=f"Docker daemon check failed: {str(e)}",
                timestamp=datetime.now(),
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
            )

    @staticmethod
    def aggregate_health_results(results: list[HealthCheckResult]) -> dict[str, Any]:
        """Aggregate multiple health check results."""
        if not results:
            return {
                "overall_status": "unknown",
                "total_checks": 0,
                "healthy_count": 0,
                "unhealthy_count": 0,
                "unknown_count": 0,
                "average_duration_ms": 0.0,
            }

        healthy_count = sum(1 for r in results if r.status == "healthy")
        unhealthy_count = sum(1 for r in results if r.status == "unhealthy")
        unknown_count = sum(1 for r in results if r.status == "unknown")

        # Determine overall status
        if unhealthy_count > 0:
            overall_status = "unhealthy"
        elif unknown_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        avg_duration = sum(r.duration_ms for r in results) / len(results)

        return {
            "overall_status": overall_status,
            "total_checks": len(results),
            "healthy_count": healthy_count,
            "unhealthy_count": unhealthy_count,
            "unknown_count": unknown_count,
            "average_duration_ms": round(avg_duration, 2),
            "details": [
                {
                    "component": r.component,
                    "status": r.status,
                    "message": r.message,
                    "duration_ms": r.duration_ms,
                }
                for r in results
            ],
        }

    @staticmethod
    def _calculate_uptime(started_at: str) -> str:
        """Calculate container uptime."""
        if not started_at:
            return "unknown"

        try:
            start_time = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            uptime = datetime.now(start_time.tzinfo) - start_time

            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)

            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"

        except Exception:
            return "unknown"

    @staticmethod
    def create_health_report(health_results: list[HealthCheckResult]) -> str:
        """Create a formatted health report."""
        if not health_results:
            return "No health checks performed."

        aggregated = HealthUtils.aggregate_health_results(health_results)

        report = []
        report.append("=== Docker Health Report ===")
        report.append(f"Overall Status: {aggregated['overall_status'].upper()}")
        report.append(f"Total Checks: {aggregated['total_checks']}")
        report.append(f"Healthy: {aggregated['healthy_count']}")
        report.append(f"Unhealthy: {aggregated['unhealthy_count']}")
        report.append(f"Unknown: {aggregated['unknown_count']}")
        report.append(f"Average Duration: {aggregated['average_duration_ms']}ms")
        report.append("")

        report.append("=== Component Details ===")
        for result in health_results:
            status_symbol = {"healthy": "✓", "unhealthy": "✗", "unknown": "?"}.get(
                result.status, "?"
            )

            report.append(
                f"{status_symbol} {result.component}: {result.message} "
                f"({result.duration_ms:.1f}ms)"
            )

        return "\n".join(report)
