"""Enhanced error handling and resilience patterns for agents.

This module provides advanced error handling capabilities including:
- Circuit breaker pattern for external service calls
- Exponential backoff with jitter for retries
- Error aggregation and pattern recognition
- Recovery strategies and fallback mechanisms
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorMetrics:
    """Error tracking metrics."""

    total_errors: int = 0
    consecutive_errors: int = 0
    error_rate: float = 0.0
    last_error_time: Optional[datetime] = None
    recovery_attempts: int = 0
    error_patterns: Dict[str, int] = field(default_factory=dict)


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: List[type] = field(default_factory=lambda: [Exception])


class CircuitBreaker:
    """Circuit breaker implementation for external service calls."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying half-open
            expected_exception: Exception type to track
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.next_attempt_time: Optional[datetime] = None

        self.logger = logging.getLogger(f"{__name__}.CircuitBreaker")

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if self._should_try_reset():
                self.state = CircuitState.HALF_OPEN
                self.logger.info("Circuit breaker transitioning to HALF_OPEN")
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")

        try:
            result = (
                await func(*args, **kwargs)
                if asyncio.iscoroutinefunction(func)
                else func(*args, **kwargs)
            )
            self._on_success()
            return result

        except self.expected_exception:
            self._on_failure()
            raise

    def _should_try_reset(self) -> bool:
        """Check if circuit breaker should try to reset."""
        if not self.last_failure_time:
            return False

        time_since_failure = datetime.now(timezone.utc) - self.last_failure_time
        return time_since_failure.total_seconds() >= self.recovery_timeout

    def _on_success(self) -> None:
        """Handle successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.logger.info("Circuit breaker CLOSED after successful recovery")

        self.failure_count = 0
        self.last_failure_time = None

    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.next_attempt_time = datetime.now(timezone.utc) + timedelta(
                seconds=self.recovery_timeout
            )
            self.logger.warning(
                f"Circuit breaker OPENED after {self.failure_count} failures"
            )


class RetryableError(Exception):
    """Exception that indicates operation should be retried."""

    pass


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""

    pass


class ErrorAggregator:
    """Aggregates and analyzes error patterns."""

    def __init__(self, window_size: int = 100):
        """Initialize error aggregator.

        Args:
            window_size: Number of recent errors to track
        """
        self.window_size = window_size
        self.errors: List[Dict[str, Any]] = []
        self.metrics = ErrorMetrics()

    def record_error(
        self,
        error: Exception,
        context: str = "",
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    ) -> None:
        """Record an error occurrence."""
        now = datetime.now(timezone.utc)

        error_record = {
            "timestamp": now,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "severity": severity,
        }

        self.errors.append(error_record)

        # Maintain window size
        if len(self.errors) > self.window_size:
            self.errors.pop(0)

        # Update metrics
        self.metrics.total_errors += 1
        self.metrics.consecutive_errors += 1
        self.metrics.last_error_time = now

        # Track error patterns
        error_key = f"{error_record['error_type']}:{context}"
        self.metrics.error_patterns[error_key] = (
            self.metrics.error_patterns.get(error_key, 0) + 1
        )

    def record_success(self) -> None:
        """Record successful operation."""
        self.metrics.consecutive_errors = 0

        # Calculate error rate over recent window
        if len(self.errors) > 0:
            recent_errors = [
                e
                for e in self.errors
                if (datetime.now(timezone.utc) - e["timestamp"]).total_seconds()
                < 300  # 5 minutes
            ]
            self.metrics.error_rate = len(recent_errors) / max(len(self.errors), 1)

    def get_error_patterns(self) -> List[Dict[str, Any]]:
        """Get common error patterns."""
        patterns = []

        for error_key, count in self.metrics.error_patterns.items():
            if count >= 3:  # Pattern threshold
                error_type, context = (
                    error_key.split(":", 1) if ":" in error_key else (error_key, "")
                )
                patterns.append(
                    {
                        "error_type": error_type,
                        "context": context,
                        "count": count,
                        "frequency": count / max(self.metrics.total_errors, 1),
                    }
                )

        return sorted(patterns, key=lambda x: x["count"], reverse=True)

    def should_trigger_alert(self) -> bool:
        """Check if error patterns warrant an alert."""
        return (
            self.metrics.consecutive_errors >= 5
            or self.metrics.error_rate > 0.3
            or any(pattern["count"] >= 10 for pattern in self.get_error_patterns())
        )


class RetryManager:
    """Advanced retry logic with exponential backoff and jitter."""

    @staticmethod
    def calculate_delay(attempt: int, config: RetryConfig) -> float:
        """Calculate delay for retry attempt."""
        delay = min(
            config.base_delay * (config.exponential_base ** (attempt - 1)),
            config.max_delay,
        )

        if config.jitter:
            # Add jitter to prevent thundering herd
            jitter_range = delay * 0.1
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)

    @staticmethod
    def is_retryable_error(error: Exception, config: RetryConfig) -> bool:
        """Check if error is retryable."""
        return any(
            isinstance(error, exc_type) for exc_type in config.retryable_exceptions
        )


def with_retry(config: Optional[RetryConfig] = None):
    """Decorator for adding retry logic to functions."""
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(1, config.max_attempts + 1):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    if not RetryManager.is_retryable_error(e, config):
                        raise

                    if attempt == config.max_attempts:
                        break

                    delay = RetryManager.calculate_delay(attempt, config)
                    logger.warning(
                        f"Attempt {attempt} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    await asyncio.sleep(delay)

            raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(1, config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    if not RetryManager.is_retryable_error(e, config):
                        raise

                    if attempt == config.max_attempts:
                        break

                    delay = RetryManager.calculate_delay(attempt, config)
                    logger.warning(
                        f"Attempt {attempt} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    time.sleep(delay)

            raise last_exception

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def with_circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: type = Exception,
):
    """Decorator for adding circuit breaker protection."""
    circuit_breaker = CircuitBreaker(
        failure_threshold, recovery_timeout, expected_exception
    )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            return await circuit_breaker.call(func, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            return asyncio.run(circuit_breaker.call(func, *args, **kwargs))

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


class ErrorHandler:
    """Comprehensive error handling for agents."""

    def __init__(self, agent_id: str):
        """Initialize error handler for an agent."""
        self.agent_id = agent_id
        self.aggregator = ErrorAggregator()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.logger = logging.getLogger(f"{__name__}.ErrorHandler.{agent_id}")

    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for a service."""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()
        return self.circuit_breakers[service_name]

    async def handle_error(
        self,
        error: Exception,
        context: str = "",
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        recovery_strategy: Optional[Callable[[], Any]] = None,
    ) -> Optional[Any]:
        """Handle an error with optional recovery strategy."""
        self.aggregator.record_error(error, context, severity)

        self.logger.error(
            f"Error in {context}: {error}",
            extra={
                "agent_id": self.agent_id,
                "error_type": type(error).__name__,
                "severity": severity.value,
                "consecutive_errors": self.aggregator.metrics.consecutive_errors,
            },
        )

        # Check if alert should be triggered
        if self.aggregator.should_trigger_alert():
            await self._trigger_alert()

        # Try recovery strategy if provided
        if recovery_strategy:
            try:
                result = (
                    await recovery_strategy()
                    if asyncio.iscoroutinefunction(recovery_strategy)
                    else recovery_strategy()
                )
                self.aggregator.record_success()
                return result
            except Exception as recovery_error:
                self.logger.error(f"Recovery strategy failed: {recovery_error}")

        return None

    async def _trigger_alert(self) -> None:
        """Trigger alert for error patterns."""
        patterns = self.aggregator.get_error_patterns()

        alert_data = {
            "agent_id": self.agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "consecutive_errors": self.aggregator.metrics.consecutive_errors,
            "error_rate": self.aggregator.metrics.error_rate,
            "top_patterns": patterns[:3],
        }

        self.logger.critical(
            f"Error alert triggered for agent {self.agent_id}", extra=alert_data
        )

        # Send alert to monitoring system
        await self._send_monitoring_alert(alert_data)

    async def _send_monitoring_alert(self, alert_data: Dict[str, Any]) -> None:
        """Send alert to monitoring system."""
        try:
            # Log to structured logging for monitoring systems to pick up
            self.logger.critical(
                "MONITORING_ALERT",
                extra={
                    "alert_type": "agent_error_pattern",
                    "alert_data": alert_data,
                    "requires_attention": True,
                    "escalation_level": self._determine_escalation_level(alert_data),
                },
            )

            # If monitoring integration is available, send to external systems
            try:
                from src.agents.monitoring import get_agent_monitor

                monitor = get_agent_monitor()
                if monitor:
                    await monitor.send_alert(
                        alert_type="error_pattern",
                        agent_id=self.agent_id,
                        data=alert_data,
                    )
            except ImportError:
                # Monitoring module not available, rely on logging
                self.logger.debug("Monitoring module not available, using logging only")

            # Store alert in knowledge graph if available
            try:
                from datetime import datetime, timezone

                # Create alert entity in knowledge graph
                alert_entity = {
                    "name": f'ErrorAlert-{self.agent_id}-{datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")}',
                    "entityType": "ErrorAlert",
                    "observations": [
                        f"Agent: {self.agent_id}",
                        f'Consecutive errors: {alert_data["consecutive_errors"]}',
                        f'Error rate: {alert_data["error_rate"]:.2f}',
                        f'Timestamp: {alert_data["timestamp"]}',
                        f'Top error patterns: {alert_data["top_patterns"]}',
                        f"Escalation level: {self._determine_escalation_level(alert_data)}",
                    ],
                }

                # Note: This would require KG integration to be available
                self.logger.info(
                    f"Alert data prepared for KG storage: {alert_entity['name']}"
                )

            except Exception as kg_error:
                self.logger.debug(f"Could not store alert in KG: {kg_error}")

        except Exception as e:
            self.logger.error(f"Failed to send monitoring alert: {e}")

    def _determine_escalation_level(self, alert_data: Dict[str, Any]) -> str:
        """Determine escalation level based on alert data."""
        consecutive_errors = alert_data.get("consecutive_errors", 0)
        error_rate = alert_data.get("error_rate", 0.0)

        if consecutive_errors >= 10 or error_rate >= 0.8:
            return "critical"
        elif consecutive_errors >= 5 or error_rate >= 0.5:
            return "high"
        elif consecutive_errors >= 3 or error_rate >= 0.3:
            return "medium"
        else:
            return "low"

    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return {
            "agent_id": self.agent_id,
            "consecutive_errors": self.aggregator.metrics.consecutive_errors,
            "error_rate": self.aggregator.metrics.error_rate,
            "last_error_time": self.aggregator.metrics.last_error_time.isoformat()
            if self.aggregator.metrics.last_error_time
            else None,
            "circuit_breakers": {
                name: {"state": cb.state.value, "failure_count": cb.failure_count}
                for name, cb in self.circuit_breakers.items()
            },
            "error_patterns": self.aggregator.get_error_patterns(),
        }
