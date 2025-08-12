"""
DRY Error Handling - Centralized Error Management

Eliminates error handling pattern duplication across database clients
and plugin implementations.
"""

import asyncio
import logging
import traceback
from typing import Dict, Any, Optional, Callable, Type, Union
from functools import wraps
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""

    CONNECTION = "connection"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    PERMISSION = "permission"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    DATA = "data"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    PLUGIN = "plugin"
    WORKFLOW = "workflow"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for error handling."""

    operation: str
    component: str
    user_data: Optional[Dict[str, Any]] = None
    system_data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class ErrorResponse:
    """Standardized error response."""

    success: bool = False
    error_code: str = "UNKNOWN_ERROR"
    error_message: str = "An unknown error occurred"
    error_category: ErrorCategory = ErrorCategory.UNKNOWN
    error_severity: ErrorSeverity = ErrorSeverity.MEDIUM
    retry_possible: bool = False
    suggested_action: Optional[str] = None
    context: Optional[ErrorContext] = None
    technical_details: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "error_category": self.error_category.value,
            "error_severity": self.error_severity.value,
            "retry_possible": self.retry_possible,
            "suggested_action": self.suggested_action,
            "timestamp": self.timestamp.isoformat() + "Z" if self.timestamp else None,
            "technical_details": self.technical_details,
        }


class ErrorHandler:
    """
    Centralized error handler eliminating error handling duplication.

    Eliminates duplication of:
    - Try/catch patterns
    - Error logging
    - Error classification
    - Retry logic
    - Error response formatting
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._error_patterns: Dict[Type[Exception], ErrorCategory] = {}
        self._retry_strategies: Dict[ErrorCategory, int] = {}
        self._error_count: Dict[str, int] = {}

        # Default error mappings
        self._setup_default_mappings()

    def _setup_default_mappings(self):
        """Setup default error category mappings."""
        import requests
        from arango.exceptions import ArangoError

        # Connection errors
        self._error_patterns.update(
            {
                ConnectionError: ErrorCategory.CONNECTION,
                TimeoutError: ErrorCategory.TIMEOUT,
                requests.exceptions.ConnectionError: ErrorCategory.CONNECTION,
                requests.exceptions.Timeout: ErrorCategory.TIMEOUT,
                ArangoError: ErrorCategory.CONNECTION,
            }
        )

        # Validation errors
        self._error_patterns.update(
            {
                ValueError: ErrorCategory.VALIDATION,
                TypeError: ErrorCategory.VALIDATION,
                KeyError: ErrorCategory.DATA,
                IndexError: ErrorCategory.DATA,
            }
        )

        # Default retry strategies
        self._retry_strategies = {
            ErrorCategory.CONNECTION: 3,
            ErrorCategory.TIMEOUT: 2,
            ErrorCategory.RATE_LIMIT: 5,
            ErrorCategory.SYSTEM: 1,
            ErrorCategory.UNKNOWN: 1,
        }

    def register_error_pattern(
        self, exception_type: Type[Exception], category: ErrorCategory
    ):
        """Register custom error pattern mapping."""
        self._error_patterns[exception_type] = category

    def set_retry_strategy(self, category: ErrorCategory, max_retries: int):
        """Set retry strategy for error category."""
        self._retry_strategies[category] = max_retries

    def categorize_error(self, exception: Exception) -> ErrorCategory:
        """Categorize exception based on type and patterns."""
        for exc_type, category in self._error_patterns.items():
            if isinstance(exception, exc_type):
                return category

        # Check error message for patterns
        error_msg = str(exception).lower()

        if any(term in error_msg for term in ["connection", "network", "unreachable"]):
            return ErrorCategory.CONNECTION
        elif any(term in error_msg for term in ["timeout", "timed out"]):
            return ErrorCategory.TIMEOUT
        elif any(
            term in error_msg for term in ["permission", "unauthorized", "forbidden"]
        ):
            return ErrorCategory.PERMISSION
        elif any(term in error_msg for term in ["rate limit", "too many requests"]):
            return ErrorCategory.RATE_LIMIT
        elif any(term in error_msg for term in ["config", "configuration"]):
            return ErrorCategory.CONFIGURATION

        return ErrorCategory.UNKNOWN

    def determine_severity(
        self, exception: Exception, category: ErrorCategory
    ) -> ErrorSeverity:
        """Determine error severity based on type and category."""
        if category == ErrorCategory.CRITICAL:
            return ErrorSeverity.CRITICAL
        elif category in [ErrorCategory.CONNECTION, ErrorCategory.AUTHENTICATION]:
            return ErrorSeverity.HIGH
        elif category in [ErrorCategory.TIMEOUT, ErrorCategory.RATE_LIMIT]:
            return ErrorSeverity.MEDIUM
        elif category in [ErrorCategory.VALIDATION, ErrorCategory.DATA]:
            return ErrorSeverity.LOW

        # Check for critical exceptions
        if isinstance(exception, (SystemExit, KeyboardInterrupt, MemoryError)):
            return ErrorSeverity.CRITICAL

        return ErrorSeverity.MEDIUM

    def should_retry(self, category: ErrorCategory, attempt_count: int) -> bool:
        """Determine if operation should be retried."""
        max_retries = self._retry_strategies.get(category, 0)
        return attempt_count < max_retries

    def handle_error(
        self,
        exception: Exception,
        context: ErrorContext,
        include_traceback: bool = True,
    ) -> ErrorResponse:
        """
        Handle exception and create standardized error response.

        Args:
            exception: The exception that occurred
            context: Context information
            include_traceback: Whether to include technical details

        Returns:
            Standardized error response
        """
        # Categorize and assess error
        category = self.categorize_error(exception)
        severity = self.determine_severity(exception, category)

        # Track error counts
        error_key = f"{context.component}:{context.operation}:{category.value}"
        self._error_count[error_key] = self._error_count.get(error_key, 0) + 1

        # Create error code
        error_code = f"{category.value.upper()}_{type(exception).__name__.upper()}"

        # Create user-friendly message
        user_message = self._create_user_message(exception, category)

        # Determine if retry is possible
        retry_possible = category in self._retry_strategies

        # Create suggested action
        suggested_action = self._create_suggested_action(category, exception)

        # Technical details
        technical_details = None
        if include_traceback:
            technical_details = traceback.format_exc()

        # Log the error
        self._log_error(exception, context, category, severity)

        return ErrorResponse(
            success=False,
            error_code=error_code,
            error_message=user_message,
            error_category=category,
            error_severity=severity,
            retry_possible=retry_possible,
            suggested_action=suggested_action,
            context=context,
            technical_details=technical_details,
        )

    def _create_user_message(
        self, exception: Exception, category: ErrorCategory
    ) -> str:
        """Create user-friendly error message."""
        messages = {
            ErrorCategory.CONNECTION: "Unable to connect to the service. Please check your network connection.",
            ErrorCategory.TIMEOUT: "The operation timed out. Please try again.",
            ErrorCategory.AUTHENTICATION: "Authentication failed. Please check your credentials.",
            ErrorCategory.PERMISSION: "You don't have permission to perform this operation.",
            ErrorCategory.RATE_LIMIT: "Rate limit exceeded. Please wait before trying again.",
            ErrorCategory.VALIDATION: "Invalid input provided. Please check your data.",
            ErrorCategory.CONFIGURATION: "Configuration error detected. Please check your settings.",
            ErrorCategory.DATA: "Data processing error occurred.",
            ErrorCategory.SYSTEM: "A system error occurred. Please try again later.",
            ErrorCategory.PLUGIN: "Plugin execution failed.",
            ErrorCategory.WORKFLOW: "Workflow execution failed.",
        }

        return messages.get(category, f"An error occurred: {str(exception)}")

    def _create_suggested_action(
        self, category: ErrorCategory, exception: Exception
    ) -> Optional[str]:
        """Create suggested action for error recovery."""
        suggestions = {
            ErrorCategory.CONNECTION: "Check network connectivity and service status",
            ErrorCategory.TIMEOUT: "Increase timeout values or retry with smaller operations",
            ErrorCategory.AUTHENTICATION: "Verify credentials and permissions",
            ErrorCategory.RATE_LIMIT: "Wait before retrying or reduce request frequency",
            ErrorCategory.VALIDATION: "Validate input data and correct any errors",
            ErrorCategory.CONFIGURATION: "Review and correct configuration settings",
            ErrorCategory.SYSTEM: "Contact system administrator if issue persists",
        }

        return suggestions.get(category)

    def _log_error(
        self,
        exception: Exception,
        context: ErrorContext,
        category: ErrorCategory,
        severity: ErrorSeverity,
    ):
        """Log error with appropriate level."""
        log_message = (
            f"Error in {context.component}.{context.operation}: {str(exception)}"
        )

        # Log with appropriate level based on severity
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, exc_info=True)
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(log_message, exc_info=True)
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        return {
            "total_errors": sum(self._error_count.values()),
            "error_breakdown": self._error_count.copy(),
            "top_errors": sorted(
                self._error_count.items(), key=lambda x: x[1], reverse=True
            )[:10],
        }


def with_error_handling(
    operation: str,
    component: str,
    error_handler: Optional[ErrorHandler] = None,
    max_retries: int = 0,
    retry_delay: float = 1.0,
    include_traceback: bool = True,
):
    """
    Decorator for automatic error handling with retry logic.

    Eliminates try/catch boilerplate across functions.

    Args:
        operation: Name of the operation
        component: Component name
        error_handler: Error handler instance
        max_retries: Maximum retry attempts
        retry_delay: Delay between retries
        include_traceback: Include technical details
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            handler = error_handler or ErrorHandler()
            context = ErrorContext(operation=operation, component=component)

            for attempt in range(max_retries + 1):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)

                except Exception as e:
                    error_response = handler.handle_error(e, context, include_traceback)

                    # Check if we should retry
                    if attempt < max_retries and error_response.retry_possible:
                        handler.logger.info(
                            f"Retrying {operation} (attempt {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(
                            retry_delay * (attempt + 1)
                        )  # Exponential backoff
                        continue

                    # No more retries or not retryable
                    return error_response

            # Should never reach here
            return ErrorResponse(
                error_message="Maximum retries exceeded",
                error_category=ErrorCategory.SYSTEM,
            )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            handler = error_handler or ErrorHandler()
            context = ErrorContext(operation=operation, component=component)

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    error_response = handler.handle_error(e, context, include_traceback)

                    # Check if we should retry
                    if attempt < max_retries and error_response.retry_possible:
                        handler.logger.info(
                            f"Retrying {operation} (attempt {attempt + 1}/{max_retries})"
                        )
                        import time

                        time.sleep(retry_delay * (attempt + 1))
                        continue

                    return error_response

            return ErrorResponse(
                error_message="Maximum retries exceeded",
                error_category=ErrorCategory.SYSTEM,
            )

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def safe_execute(
    func: Callable,
    error_handler: Optional[ErrorHandler] = None,
    context: Optional[ErrorContext] = None,
    default_return: Any = None,
) -> Union[Any, ErrorResponse]:
    """
    Safely execute a function with error handling.

    Args:
        func: Function to execute
        error_handler: Error handler instance
        context: Error context
        default_return: Default return value on error

    Returns:
        Function result or ErrorResponse on error
    """
    handler = error_handler or ErrorHandler()
    ctx = context or ErrorContext(operation="safe_execute", component="unknown")

    try:
        return func()
    except Exception as e:
        error_response = handler.handle_error(e, ctx)
        return default_return if default_return is not None else error_response


# Global error handler
_global_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance."""
    return _global_error_handler


def handle_error(exception: Exception, operation: str, component: str) -> ErrorResponse:
    """Handle error using global error handler."""
    context = ErrorContext(operation=operation, component=component)
    return _global_error_handler.handle_error(exception, context)


def register_error_pattern(exception_type: Type[Exception], category: ErrorCategory):
    """Register error pattern with global handler."""
    _global_error_handler.register_error_pattern(exception_type, category)


def get_error_stats() -> Dict[str, Any]:
    """Get error statistics from global handler."""
    return _global_error_handler.get_error_stats()
