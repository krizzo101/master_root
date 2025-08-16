"""
Custom exceptions for the KG-DB Optimization System

Provides a hierarchical exception structure for comprehensive error handling
and debugging support across all optimization components.
"""

from __future__ import annotations
from typing import Any, Dict, Optional


class OptimizationError(Exception):
    """Base exception for all optimization system errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.timestamp = None  # Will be set by performance monitor

    def __str__(self) -> str:
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} (Details: {detail_str})"
        return self.message


class DatabaseConnectionError(OptimizationError):
    """Raised when database connection or operation fails."""

    def __init__(
        self,
        message: str,
        database_path: Optional[str] = None,
        operation: Optional[str] = None,
    ) -> None:
        details = {}
        if database_path:
            details["database_path"] = database_path
        if operation:
            details["operation"] = operation
        super().__init__(message, details)


class KGOperationError(OptimizationError):
    """Raised when Knowledge Graph operations fail."""

    def __init__(
        self,
        message: str,
        entity_name: Optional[str] = None,
        operation: Optional[str] = None,
        retry_count: int = 0,
    ) -> None:
        details = {"retry_count": retry_count}
        if entity_name:
            details["entity_name"] = entity_name
        if operation:
            details["operation"] = operation
        super().__init__(message, details)


class CacheError(OptimizationError):
    """Raised when cache operations fail."""

    def __init__(
        self,
        message: str,
        cache_key: Optional[str] = None,
        operation: Optional[str] = None,
    ) -> None:
        details = {}
        if cache_key:
            details["cache_key"] = cache_key
        if operation:
            details["operation"] = operation
        super().__init__(message, details)


class PerformanceError(OptimizationError):
    """Raised when performance thresholds are violated."""

    def __init__(
        self,
        message: str,
        metric: Optional[str] = None,
        threshold: Optional[float] = None,
        actual: Optional[float] = None,
    ) -> None:
        details = {}
        if metric:
            details["metric"] = metric
        if threshold is not None:
            details["threshold"] = threshold
        if actual is not None:
            details["actual"] = actual
        super().__init__(message, details)


class ResourceRoutingError(OptimizationError):
    """Raised when resource routing fails."""

    def __init__(
        self,
        message: str,
        request_type: Optional[str] = None,
        available_resources: Optional[list[str]] = None,
    ) -> None:
        details = {}
        if request_type:
            details["request_type"] = request_type
        if available_resources:
            details["available_resources"] = available_resources
        super().__init__(message, details)


class ValidationError(OptimizationError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        expected_type: Optional[str] = None,
    ) -> None:
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        if expected_type:
            details["expected_type"] = expected_type
        super().__init__(message, details)


class TimeoutError(OptimizationError):
    """Raised when operations exceed timeout thresholds."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        details = {}
        if operation:
            details["operation"] = operation
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        super().__init__(message, details)
