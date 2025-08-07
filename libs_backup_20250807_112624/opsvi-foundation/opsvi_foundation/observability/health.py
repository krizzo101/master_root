"""
Health check system for monitoring system health.

Provides health endpoints, dependency checks, readiness probes,
and comprehensive health monitoring capabilities.
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from opsvi_foundation.patterns import ComponentError


class HealthError(ComponentError):
    """Raised when health check fails."""


class HealthStatus(Enum):
    """Health status values."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check configuration and result."""

    name: str
    description: str = ""
    timeout: float = 30.0
    critical: bool = True
    status: HealthStatus = HealthStatus.UNKNOWN
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    last_check: float | None = None
    check_duration: float | None = None


class HealthChecker(ABC):
    """Abstract base class for health checkers."""

    def __init__(
        self,
        name: str,
        description: str = "",
        timeout: float = 30.0,
        critical: bool = True,
    ):
        """
        Initialize health checker.

        Args:
            name: Health check name
            description: Health check description
            timeout: Health check timeout
            critical: Whether this check is critical
        """
        self.name = name
        self.description = description
        self.timeout = timeout
        self.critical = critical

    @abstractmethod
    async def check(self) -> HealthCheck:
        """
        Perform health check.

        Returns:
            Health check result
        """


class PingHealthChecker(HealthChecker):
    """Ping-based health checker."""

    def __init__(self, host: str, port: int = 80, **kwargs):
        """
        Initialize ping health checker.

        Args:
            host: Host to ping
            port: Port to check
            **kwargs: Additional arguments
        """
        super().__init__(f"ping_{host}_{port}", f"Ping {host}:{port}", **kwargs)
        self.host = host
        self.port = port

    async def check(self) -> HealthCheck:
        """Perform ping health check."""
        start_time = time.time()

        try:
            # Simple socket connection test
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.timeout,
            )
            writer.close()
            await writer.wait_closed()

            duration = time.time() - start_time
            return HealthCheck(
                name=self.name,
                description=self.description,
                timeout=self.timeout,
                critical=self.critical,
                status=HealthStatus.HEALTHY,
                message=f"Successfully connected to {self.host}:{self.port}",
                details={
                    "host": self.host,
                    "port": self.port,
                    "response_time": duration,
                },
                last_check=start_time,
                check_duration=duration,
            )
        except Exception as e:
            duration = time.time() - start_time
            return HealthCheck(
                name=self.name,
                description=self.description,
                timeout=self.timeout,
                critical=self.critical,
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to connect to {self.host}:{self.port}: {e!s}",
                details={"host": self.host, "port": self.port, "error": str(e)},
                last_check=start_time,
                check_duration=duration,
            )


class HttpHealthChecker(HealthChecker):
    """HTTP-based health checker."""

    def __init__(self, url: str, expected_status: int = 200, **kwargs):
        """
        Initialize HTTP health checker.

        Args:
            url: URL to check
            expected_status: Expected HTTP status code
            **kwargs: Additional arguments
        """
        super().__init__(f"http_{url}", f"HTTP check {url}", **kwargs)
        self.url = url
        self.expected_status = expected_status

    async def check(self) -> HealthCheck:
        """Perform HTTP health check."""
        start_time = time.time()

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await asyncio.wait_for(
                    client.get(self.url),
                    timeout=self.timeout,
                )

            duration = time.time() - start_time
            status = (
                HealthStatus.HEALTHY
                if response.status_code == self.expected_status
                else HealthStatus.UNHEALTHY
            )

            return HealthCheck(
                name=self.name,
                description=self.description,
                timeout=self.timeout,
                critical=self.critical,
                status=status,
                message=f"HTTP {response.status_code} from {self.url}",
                details={
                    "url": self.url,
                    "status_code": response.status_code,
                    "expected_status": self.expected_status,
                    "response_time": duration,
                },
                last_check=start_time,
                check_duration=duration,
            )
        except Exception as e:
            duration = time.time() - start_time
            return HealthCheck(
                name=self.name,
                description=self.description,
                timeout=self.timeout,
                critical=self.critical,
                status=HealthStatus.UNHEALTHY,
                message=f"HTTP check failed for {self.url}: {e!s}",
                details={"url": self.url, "error": str(e)},
                last_check=start_time,
                check_duration=duration,
            )


class DatabaseHealthChecker(HealthChecker):
    """Database health checker."""

    def __init__(self, connection_func: Callable, **kwargs):
        """
        Initialize database health checker.

        Args:
            connection_func: Function to test database connection
            **kwargs: Additional arguments
        """
        super().__init__("database", "Database connectivity check", **kwargs)
        self.connection_func = connection_func

    async def check(self) -> HealthCheck:
        """Perform database health check."""
        start_time = time.time()

        try:
            if asyncio.iscoroutinefunction(self.connection_func):
                await asyncio.wait_for(self.connection_func(), timeout=self.timeout)
            else:
                loop = asyncio.get_event_loop()
                await asyncio.wait_for(
                    loop.run_in_executor(None, self.connection_func),
                    timeout=self.timeout,
                )

            duration = time.time() - start_time
            return HealthCheck(
                name=self.name,
                description=self.description,
                timeout=self.timeout,
                critical=self.critical,
                status=HealthStatus.HEALTHY,
                message="Database connection successful",
                details={"response_time": duration},
                last_check=start_time,
                check_duration=duration,
            )
        except Exception as e:
            duration = time.time() - start_time
            return HealthCheck(
                name=self.name,
                description=self.description,
                timeout=self.timeout,
                critical=self.critical,
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {e!s}",
                details={"error": str(e)},
                last_check=start_time,
                check_duration=duration,
            )


class CustomHealthChecker(HealthChecker):
    """Custom health checker for user-defined checks."""

    def __init__(self, name: str, check_func: Callable, **kwargs):
        """
        Initialize custom health checker.

        Args:
            name: Health check name
            check_func: Function to perform health check
            **kwargs: Additional arguments
        """
        super().__init__(name, **kwargs)
        self.check_func = check_func

    async def check(self) -> HealthCheck:
        """Perform custom health check."""
        start_time = time.time()

        try:
            if asyncio.iscoroutinefunction(self.check_func):
                result = await asyncio.wait_for(self.check_func(), timeout=self.timeout)
            else:
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, self.check_func),
                    timeout=self.timeout,
                )

            duration = time.time() - start_time

            # Handle different result types
            if isinstance(result, HealthCheck):
                result.last_check = start_time
                result.check_duration = duration
                return result
            if isinstance(result, bool):
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                return HealthCheck(
                    name=self.name,
                    description=self.description,
                    timeout=self.timeout,
                    critical=self.critical,
                    status=status,
                    message="Custom health check completed",
                    details={"result": result},
                    last_check=start_time,
                    check_duration=duration,
                )
            return HealthCheck(
                name=self.name,
                description=self.description,
                timeout=self.timeout,
                critical=self.critical,
                status=HealthStatus.HEALTHY,
                message="Custom health check completed",
                details={"result": result},
                last_check=start_time,
                check_duration=duration,
            )
        except Exception as e:
            duration = time.time() - start_time
            return HealthCheck(
                name=self.name,
                description=self.description,
                timeout=self.timeout,
                critical=self.critical,
                status=HealthStatus.UNHEALTHY,
                message=f"Custom health check failed: {e!s}",
                details={"error": str(e)},
                last_check=start_time,
                check_duration=duration,
            )


class HealthMonitor:
    """Main health monitoring system."""

    def __init__(self):
        """Initialize health monitor."""
        self.checkers: dict[str, HealthChecker] = {}
        self.last_results: dict[str, HealthCheck] = {}
        self.auto_refresh: bool = False
        self.refresh_interval: float = 60.0  # 1 minute
        self._refresh_task: asyncio.Task | None = None

    def add_checker(self, checker: HealthChecker) -> None:
        """
        Add health checker.

        Args:
            checker: Health checker to add
        """
        self.checkers[checker.name] = checker

    def remove_checker(self, name: str) -> None:
        """
        Remove health checker.

        Args:
            name: Health checker name
        """
        self.checkers.pop(name, None)
        self.last_results.pop(name, None)

    async def run_check(self, name: str) -> HealthCheck:
        """
        Run specific health check.

        Args:
            name: Health checker name

        Returns:
            Health check result

        Raises:
            ValueError: If checker not found
        """
        if name not in self.checkers:
            raise ValueError(f"Health checker '{name}' not found")

        checker = self.checkers[name]
        result = await checker.check()
        self.last_results[name] = result
        return result

    async def run_all_checks(self) -> dict[str, HealthCheck]:
        """
        Run all health checks.

        Returns:
            Dictionary of health check results
        """
        tasks = []
        for name in self.checkers:
            tasks.append(self.run_check(name))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        for name, result in zip(self.checkers.keys(), results, strict=False):
            if isinstance(result, Exception):
                self.last_results[name] = HealthCheck(
                    name=name,
                    description=self.checkers[name].description,
                    timeout=self.checkers[name].timeout,
                    critical=self.checkers[name].critical,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {result!s}",
                    details={"error": str(result)},
                )
            else:
                self.last_results[name] = result

        return self.last_results.copy()

    def get_overall_status(self) -> HealthStatus:
        """
        Get overall health status.

        Returns:
            Overall health status
        """
        if not self.last_results:
            return HealthStatus.UNKNOWN

        has_critical_failure = any(
            result.status == HealthStatus.UNHEALTHY and result.critical
            for result in self.last_results.values()
        )

        if has_critical_failure:
            return HealthStatus.UNHEALTHY

        has_degraded = any(
            result.status == HealthStatus.DEGRADED
            for result in self.last_results.values()
        )

        if has_degraded:
            return HealthStatus.DEGRADED

        all_healthy = all(
            result.status == HealthStatus.HEALTHY
            for result in self.last_results.values()
        )

        return HealthStatus.HEALTHY if all_healthy else HealthStatus.DEGRADED

    def get_health_summary(self) -> dict[str, Any]:
        """
        Get health summary.

        Returns:
            Health summary dictionary
        """
        overall_status = self.get_overall_status()

        return {
            "status": overall_status.value,
            "timestamp": time.time(),
            "checks": {
                name: {
                    "status": result.status.value,
                    "message": result.message,
                    "critical": result.critical,
                    "last_check": result.last_check,
                    "check_duration": result.check_duration,
                }
                for name, result in self.last_results.items()
            },
        }

    def start_auto_refresh(self, interval: float | None = None) -> None:
        """
        Start automatic health check refresh.

        Args:
            interval: Refresh interval in seconds
        """
        if interval is not None:
            self.refresh_interval = interval

        if not self.auto_refresh:
            self.auto_refresh = True
            self._refresh_task = asyncio.create_task(self._refresh_loop())

    def stop_auto_refresh(self) -> None:
        """Stop automatic health check refresh."""
        self.auto_refresh = False
        if self._refresh_task:
            self._refresh_task.cancel()
            self._refresh_task = None

    async def _refresh_loop(self) -> None:
        """Background refresh loop."""
        while self.auto_refresh:
            try:
                await self.run_all_checks()
                await asyncio.sleep(self.refresh_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error and continue
                print(f"Health check refresh error: {e}")
                await asyncio.sleep(self.refresh_interval)


class HealthEndpoint:
    """Health endpoint for HTTP health checks."""

    def __init__(self, monitor: HealthMonitor, path: str = "/health"):
        """
        Initialize health endpoint.

        Args:
            monitor: Health monitor
            path: Endpoint path
        """
        self.monitor = monitor
        self.path = path

    async def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Handle health check request.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        # Run health checks
        await self.monitor.run_all_checks()

        # Get summary
        summary = self.monitor.get_health_summary()
        overall_status = self.monitor.get_overall_status()

        # Determine HTTP status code
        if overall_status == HealthStatus.HEALTHY:
            status_code = 200
        elif overall_status == HealthStatus.DEGRADED:
            status_code = 200  # Still responding but degraded
        else:
            status_code = 503  # Service unavailable

        return {
            "status_code": status_code,
            "headers": {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
            },
            "body": summary,
        }


# Global health monitor
health_monitor = HealthMonitor()


def health_check(
    name: str,
    description: str = "",
    timeout: float = 30.0,
    critical: bool = True,
):
    """
    Decorator for creating health checks from functions.

    Args:
        name: Health check name
        description: Health check description
        timeout: Health check timeout
        critical: Whether this check is critical
    """

    def decorator(func):
        checker = CustomHealthChecker(
            name,
            func,
            description=description,
            timeout=timeout,
            critical=critical,
        )
        health_monitor.add_checker(checker)
        return func

    return decorator
