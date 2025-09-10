"""
Error boundary implementation for fault isolation.
Provides error handling, retries, and graceful degradation.
"""

from typing import Any, Callable, Dict, Optional, Type, Union

from ..utils.enhanced_logging import get_logger, log_agent_event

logger = get_logger(__name__)
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""

    CRITICAL = "critical"  # System-wide failure
    HIGH = "high"  # Component failure
    MEDIUM = "medium"  # Task failure
    LOW = "low"  # Recoverable error


@dataclass
class ErrorResult:
    """Encapsulates error information"""

    error: Exception
    severity: ErrorSeverity
    context: Dict[str, Any]
    recoverable: bool
    suggested_action: Optional[str] = None


class ErrorBoundary:
    """Implements error boundary pattern for fault isolation"""

    def __init__(
        self,
        propagate_critical: bool = True,
        max_retries: int = 3,
        fallback_handler: Optional[Callable] = None,
    ):
        self.propagate_critical = propagate_critical
        self.max_retries = max_retries
        self.fallback_handler = fallback_handler
        self.error_handlers: Dict[Type[Exception], Callable] = {}

    def register_handler(self, error_type: Type[Exception], handler: Callable):
        """Register custom error handler for specific exception type"""
        self.error_handlers[error_type] = handler

    async def execute_with_boundary(
        self, func: Callable, *args, context: Dict[str, Any] = None, **kwargs
    ) -> Union[Any, ErrorResult]:
        """Execute function within error boundary"""
        retries = 0
        last_error = None

        while retries < self.max_retries:
            try:
                # Execute the function
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            except Exception as e:
                last_error = e
                severity = self._classify_error(e)

                # Check for custom handler
                handler = self._get_handler(e)
                if handler:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            return await handler(e, context)
                        else:
                            return handler(e, context)
                    except Exception as handler_error:
                        logger.error(f"Error handler failed: {handler_error}")

                # Handle based on severity
                if severity == ErrorSeverity.CRITICAL and self.propagate_critical:
                    logger.critical(f"Critical error, propagating: {e}")
                    raise

                elif severity in [ErrorSeverity.HIGH, ErrorSeverity.MEDIUM]:
                    retries += 1
                    if retries < self.max_retries:
                        await asyncio.sleep(2**retries)  # Exponential backoff
                        logger.warning(f"Retrying after {severity.value} error: {e}")
                        continue

                # Low severity or max retries reached
                break

        # Create error result
        error_result = ErrorResult(
            error=last_error,
            severity=self._classify_error(last_error),
            context=context or {},
            recoverable=self._is_recoverable(last_error),
            suggested_action=self._suggest_action(last_error),
        )

        # Try fallback handler
        if self.fallback_handler:
            try:
                if asyncio.iscoroutinefunction(self.fallback_handler):
                    return await self.fallback_handler(error_result)
                else:
                    return self.fallback_handler(error_result)
            except Exception as fallback_error:
                logger.error(f"Fallback handler failed: {fallback_error}")

        return error_result

    def _classify_error(self, error: Exception) -> ErrorSeverity:
        """Classify error severity based on type and content"""
        if isinstance(error, (SystemExit, KeyboardInterrupt)):
            return ErrorSeverity.CRITICAL
        elif isinstance(error, (MemoryError, RecursionError)):
            return ErrorSeverity.CRITICAL
        elif isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorSeverity.HIGH
        elif isinstance(error, (ValueError, TypeError)):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    def _is_recoverable(self, error: Exception) -> bool:
        """Determine if error is recoverable"""
        non_recoverable = (SystemExit, KeyboardInterrupt, MemoryError, RecursionError)
        return not isinstance(error, non_recoverable)

    def _suggest_action(self, error: Exception) -> Optional[str]:
        """Suggest recovery action for error"""
        if isinstance(error, ConnectionError):
            return "Check network connectivity and retry"
        elif isinstance(error, TimeoutError):
            return "Increase timeout or optimize operation"
        elif isinstance(error, MemoryError):
            return "Reduce memory usage or increase available memory"
        elif isinstance(error, ValueError):
            return "Check input validation and data types"
        elif isinstance(error, TypeError):
            return "Verify function signatures and argument types"
        return None

    def _get_handler(self, error: Exception) -> Optional[Callable]:
        """Get custom handler for error type"""
        for error_type, handler in self.error_handlers.items():
            if isinstance(error, error_type):
                return handler
        return None


class CompositeErrorBoundary:
    """Composite error boundary for managing multiple boundaries"""

    def __init__(self):
        self.boundaries: Dict[str, ErrorBoundary] = {}

    def add_boundary(self, name: str, boundary: ErrorBoundary):
        """Add a named error boundary"""
        self.boundaries[name] = boundary

    def get_boundary(self, name: str) -> Optional[ErrorBoundary]:
        """Get a named error boundary"""
        return self.boundaries.get(name)

    async def execute_with_boundary(
        self, boundary_name: str, func: Callable, *args, **kwargs
    ) -> Union[Any, ErrorResult]:
        """Execute function with named boundary"""
        boundary = self.boundaries.get(boundary_name)
        if not boundary:
            raise ValueError(f"Boundary not found: {boundary_name}")

        return await boundary.execute_with_boundary(func, *args, **kwargs)
