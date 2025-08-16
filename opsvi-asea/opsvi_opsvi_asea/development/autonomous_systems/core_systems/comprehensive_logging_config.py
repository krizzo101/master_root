#!/usr/bin/env python3
"""
Comprehensive Logging Configuration for Autonomous Systems

This module provides centralized, detailed logging configuration for all autonomous systems
components. It includes structured logging, multiple handlers, and debug-level granularity
for rapid error identification and remediation.

Features:
- Structured logging with consistent format
- Multiple log levels and handlers
- File rotation and retention
- Debug mode with detailed tracing
- Performance logging
- Error tracking with context
- Correlation IDs for request tracing
"""

import logging
import logging.handlers
import sys
import os
import json
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import uuid


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs for better parsing and analysis."""

    def format(self, record):
        """Format log record as structured JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "process_id": os.getpid(),
            "thread_id": record.thread,
        }

        # Add correlation ID if available
        if hasattr(record, "correlation_id"):
            log_entry["correlation_id"] = record.correlation_id

        # Add context data if available
        if hasattr(record, "context"):
            log_entry["context"] = record.context

        # Add performance metrics if available
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms

        # Add error details if this is an exception
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_entry, default=str)


class ContextualFormatter(logging.Formatter):
    """Human-readable formatter with contextual information."""

    def format(self, record):
        """Format log record with rich contextual information."""
        # Base format
        formatted = super().format(record)

        # Add correlation ID if available
        if hasattr(record, "correlation_id"):
            formatted = f"[{record.correlation_id}] {formatted}"

        # Add context if available
        if hasattr(record, "context"):
            context_str = json.dumps(record.context, default=str, separators=(",", ":"))
            formatted = f"{formatted} | Context: {context_str}"

        # Add performance info if available
        if hasattr(record, "duration_ms"):
            formatted = f"{formatted} | Duration: {record.duration_ms}ms"

        return formatted


class AutonomousSystemsLogger:
    """
    Comprehensive logging system for autonomous systems components.

    Provides structured logging, performance tracking, error context,
    and debug capabilities for rapid issue identification and resolution.
    """

    def __init__(
        self,
        component_name: str,
        log_level: str = "INFO",
        enable_file_logging: bool = True,
        enable_structured_logging: bool = True,
        log_directory: Optional[str] = None,
    ):
        """
        Initialize comprehensive logging for a component.

        Args:
            component_name: Name of the component (e.g., 'external_reasoning_service')
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_file_logging: Whether to log to files
            enable_structured_logging: Whether to use JSON structured logging
            log_directory: Custom log directory (defaults to autonomous_systems/logs)
        """
        self.component_name = component_name
        self.log_level = getattr(logging, log_level.upper())
        self.enable_file_logging = enable_file_logging
        self.enable_structured_logging = enable_structured_logging

        # Set up log directory
        if log_directory:
            self.log_directory = Path(log_directory)
        else:
            self.log_directory = Path(__file__).parent.parent / "logs"

        self.log_directory.mkdir(exist_ok=True)

        # Initialize logger
        self.logger = logging.getLogger(component_name)
        self.logger.setLevel(self.log_level)

        # Clear existing handlers to avoid duplication
        self.logger.handlers.clear()

        # Set up handlers
        self._setup_console_handler()
        if self.enable_file_logging:
            self._setup_file_handlers()

        # Performance tracking
        self.operation_start_times = {}

    def _setup_console_handler(self):
        """Set up console logging handler."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)

        if self.enable_structured_logging:
            console_handler.setFormatter(StructuredFormatter())
        else:
            formatter = ContextualFormatter(
                "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
            )
            console_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)

    def _setup_file_handlers(self):
        """Set up file logging handlers with rotation."""
        # Main log file (all levels)
        main_log_file = self.log_directory / f"{self.component_name}.log"
        main_handler = logging.handlers.RotatingFileHandler(
            main_log_file, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        main_handler.setLevel(logging.DEBUG)

        # Error log file (errors only)
        error_log_file = self.log_directory / f"{self.component_name}_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file, maxBytes=5 * 1024 * 1024, backupCount=3
        )
        error_handler.setLevel(logging.ERROR)

        # Performance log file (with timing info)
        perf_log_file = self.log_directory / f"{self.component_name}_performance.log"
        perf_handler = logging.handlers.RotatingFileHandler(
            perf_log_file, maxBytes=5 * 1024 * 1024, backupCount=3
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.addFilter(lambda record: hasattr(record, "duration_ms"))

        # Set formatters
        if self.enable_structured_logging:
            formatter = StructuredFormatter()
        else:
            formatter = ContextualFormatter(
                "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
            )

        main_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        perf_handler.setFormatter(formatter)

        # Add handlers
        self.logger.addHandler(main_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(perf_handler)

    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self.logger

    def log_with_context(
        self,
        level: str,
        message: str,
        context: Dict[str, Any] = None,
        correlation_id: str = None,
    ):
        """
        Log message with additional context information.

        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Log message
            context: Additional context data
            correlation_id: Correlation ID for request tracing
        """
        log_method = getattr(self.logger, level.lower())

        # Create log record with extra data
        extra = {}
        if context:
            extra["context"] = context
        if correlation_id:
            extra["correlation_id"] = correlation_id

        log_method(message, extra=extra)

    def start_operation(
        self, operation_name: str, context: Dict[str, Any] = None
    ) -> str:
        """
        Start tracking an operation for performance logging.

        Args:
            operation_name: Name of the operation
            context: Additional context data

        Returns:
            Correlation ID for the operation
        """
        correlation_id = str(uuid.uuid4())
        start_time = datetime.now()

        self.operation_start_times[correlation_id] = {
            "operation": operation_name,
            "start_time": start_time,
            "context": context or {},
        }

        self.log_with_context(
            "info",
            f"Starting operation: {operation_name}",
            context={"operation": operation_name, **context}
            if context
            else {"operation": operation_name},
            correlation_id=correlation_id,
        )

        return correlation_id

    def end_operation(
        self,
        correlation_id: str,
        success: bool = True,
        result_context: Dict[str, Any] = None,
    ):
        """
        End operation tracking and log performance metrics.

        Args:
            correlation_id: Correlation ID from start_operation
            success: Whether the operation succeeded
            result_context: Additional result context
        """
        if correlation_id not in self.operation_start_times:
            self.logger.warning(
                f"Unknown correlation ID for operation end: {correlation_id}"
            )
            return

        operation_info = self.operation_start_times.pop(correlation_id)
        end_time = datetime.now()
        duration_ms = int(
            (end_time - operation_info["start_time"]).total_seconds() * 1000
        )

        context = {
            "operation": operation_info["operation"],
            "success": success,
            "duration_ms": duration_ms,
            **operation_info["context"],
        }

        if result_context:
            context.update(result_context)

        level = "info" if success else "error"
        status = "completed" if success else "failed"

        # Log with performance data
        log_record = self.logger.makeRecord(
            self.logger.name,
            getattr(logging, level.upper()),
            __file__,
            0,
            f"Operation {status}: {operation_info['operation']}",
            (),
            None,
        )
        log_record.correlation_id = correlation_id
        log_record.context = context
        log_record.duration_ms = duration_ms

        self.logger.handle(log_record)

    def log_api_call(
        self,
        api_name: str,
        endpoint: str,
        method: str = "POST",
        request_data: Dict[str, Any] = None,
        response_data: Dict[str, Any] = None,
        success: bool = True,
        error: str = None,
        duration_ms: int = None,
    ):
        """
        Log API call details for debugging and monitoring.

        Args:
            api_name: Name of the API (e.g., 'OpenAI', 'ArangoDB')
            endpoint: API endpoint
            method: HTTP method
            request_data: Request data (sensitive data will be masked)
            response_data: Response data
            success: Whether the call succeeded
            error: Error message if failed
            duration_ms: Call duration in milliseconds
        """
        context = {
            "api_name": api_name,
            "endpoint": endpoint,
            "method": method,
            "success": success,
        }

        # Mask sensitive data in request
        if request_data:
            masked_request = self._mask_sensitive_data(request_data)
            context["request_data"] = masked_request

        # Include response data (first 500 chars if string)
        if response_data:
            if isinstance(response_data, str) and len(response_data) > 500:
                context["response_preview"] = response_data[:500] + "..."
            else:
                context["response_data"] = response_data

        if error:
            context["error"] = error

        if duration_ms:
            context["duration_ms"] = duration_ms

        level = "info" if success else "error"
        message = f"API call {api_name} {method} {endpoint} {'succeeded' if success else 'failed'}"

        if duration_ms:
            # Create record with performance data
            log_record = self.logger.makeRecord(
                self.logger.name,
                getattr(logging, level.upper()),
                __file__,
                0,
                message,
                (),
                None,
            )
            log_record.context = context
            log_record.duration_ms = duration_ms
            self.logger.handle(log_record)
        else:
            self.log_with_context(level, message, context)

    def log_error_with_context(
        self,
        error: Exception,
        context: Dict[str, Any] = None,
        correlation_id: str = None,
    ):
        """
        Log error with full context and traceback.

        Args:
            error: Exception object
            context: Additional context data
            correlation_id: Correlation ID if part of tracked operation
        """
        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
        }

        if context:
            error_context.update(context)

        self.log_with_context(
            "error",
            f"Exception occurred: {type(error).__name__}: {str(error)}",
            error_context,
            correlation_id,
        )

    def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive data in logs."""
        sensitive_keys = ["api_key", "password", "token", "secret", "key"]

        if not isinstance(data, dict):
            return data

        masked = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                if isinstance(value, str) and len(value) > 8:
                    masked[key] = value[:4] + "****" + value[-4:]
                else:
                    masked[key] = "****"
            elif isinstance(value, dict):
                masked[key] = self._mask_sensitive_data(value)
            else:
                masked[key] = value

        return masked

    def create_child_logger(self, child_name: str) -> "AutonomousSystemsLogger":
        """
        Create a child logger with the same configuration.

        Args:
            child_name: Name for the child logger

        Returns:
            Child logger instance
        """
        full_child_name = f"{self.component_name}.{child_name}"
        return AutonomousSystemsLogger(
            component_name=full_child_name,
            log_level=logging.getLevelName(self.log_level),
            enable_file_logging=self.enable_file_logging,
            enable_structured_logging=self.enable_structured_logging,
            log_directory=str(self.log_directory),
        )


def get_logger(component_name: str, **kwargs) -> AutonomousSystemsLogger:
    """
    Factory function to get a configured logger for a component.

    Args:
        component_name: Name of the component
        **kwargs: Additional configuration options

    Returns:
        Configured logger instance
    """
    return AutonomousSystemsLogger(component_name, **kwargs)


def setup_debug_logging():
    """Enable debug-level logging for all autonomous systems components."""
    # Set root logger to DEBUG
    logging.getLogger().setLevel(logging.DEBUG)

    # Enable debug for specific modules
    debug_modules = [
        "autonomous_systems",
        "external_reasoning_service",
        "knowledge_context_gatherer",
        "autonomous_openai_client",
        "autonomous_decision_system",
    ]

    for module in debug_modules:
        logging.getLogger(module).setLevel(logging.DEBUG)

    print("🐛 Debug logging enabled for autonomous systems")


# Example usage and testing
if __name__ == "__main__":
    # Test the logging system
    logger = get_logger("test_component", log_level="DEBUG")

    # Test basic logging
    logger.log_with_context(
        "info", "Testing comprehensive logging system", {"test_param": "test_value"}
    )

    # Test operation tracking
    correlation_id = logger.start_operation("test_operation", {"param": "value"})

    # Simulate some work
    import time

    time.sleep(0.1)

    logger.end_operation(
        correlation_id, success=True, result_context={"result": "success"}
    )

    # Test API call logging
    logger.log_api_call(
        "TestAPI",
        "/test/endpoint",
        "POST",
        request_data={"api_key": "secret123", "data": "test"},
        response_data={"status": "ok"},
        success=True,
        duration_ms=150,
    )

    # Test error logging
    try:
        raise ValueError("Test error for logging")
    except Exception as e:
        logger.log_error_with_context(e, {"operation": "test_error"})

    print("✅ Logging system test completed - check logs directory")
