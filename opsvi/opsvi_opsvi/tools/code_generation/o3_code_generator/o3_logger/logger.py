"""
O3 Code Generator Logger

This module provides comprehensive logging functionality for the O3 Code Generator,
including standard logging, debug logging, and performance tracking.
"""

import json
import logging
import logging.handlers
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class LogConfig:
    """Configuration for logging system."""

    level: str = "INFO"
    log_dir: str = "logs"
    standard_log_file: str = "o3_generator.log"
    debug_log_file: str = "o3_generator_debug.log"
    error_log_file: str = "o3_generator_error.log"
    console_output: bool = True
    enable_debug_log: bool = False
    max_file_size_mb: int = 10
    backup_count: int = 5
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"


class O3Logger:
    """
    Comprehensive logging system for O3 Code Generator.

    Provides:
    - Standard application logging
    - Debug logging with detailed information
    - Error logging with stack traces
    - Performance tracking
    - Structured logging capabilities
    """

    def __init__(self, config: LogConfig):
        """
        Initialize the O3 logger.

        Args:
            config: Logging configuration
        """
        self.config = config
        self.log_dir = Path(config.log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Create correlation ID for this session
        self.correlation_id = str(uuid.uuid4())

        # Initialize loggers
        self._setup_loggers()

        # Log initialization (only in debug mode)
        if self.config.enable_debug_log and not self._is_help_mode():
            self.logger.info(
                f"O3 Logger initialized with correlation ID: {self.correlation_id}"
            )
            self.logger.info(f"Log directory: {self.log_dir.absolute()}")
            self.logger.info(f"Log level: {config.level}")
            self.logger.info(
                f"Debug logging: {'enabled' if config.enable_debug_log else 'disabled'}"
            )

    def _setup_loggers(self) -> None:
        """Setup all loggers with proper configuration."""
        # Create main logger
        self.logger = logging.getLogger("o3_generator")
        self.logger.setLevel(getattr(logging, self.config.level.upper(), logging.INFO))

        # Prevent duplicate logging by not propagating to root logger
        self.logger.propagate = False

        # Clear any existing handlers
        self.logger.handlers.clear()

        # Suppress third-party debug logs unless in debug mode
        if not self.config.enable_debug_log:
            # Suppress OpenAI client debug logs
            logging.getLogger("openai").setLevel(logging.WARNING)
            logging.getLogger("openai._base_client").setLevel(logging.WARNING)
            logging.getLogger("httpx").setLevel(logging.WARNING)
            logging.getLogger("httpcore").setLevel(logging.WARNING)
            logging.getLogger("httpcore.connection").setLevel(logging.WARNING)
            logging.getLogger("httpcore.http11").setLevel(logging.WARNING)

        # Create formatters
        standard_formatter = logging.Formatter(
            self.config.format_string, datefmt=self.config.date_format
        )

        detailed_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
            datefmt=self.config.date_format,
        )

        # Standard log file handler
        standard_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / self.config.standard_log_file,
            maxBytes=self.config.max_file_size_mb * 1024 * 1024,
            backupCount=self.config.backup_count,
            encoding="utf-8",
        )
        standard_handler.setLevel(logging.INFO)
        standard_handler.setFormatter(standard_formatter)
        self.logger.addHandler(standard_handler)

        # Error log file handler
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / self.config.error_log_file,
            maxBytes=self.config.max_file_size_mb * 1024 * 1024,
            backupCount=self.config.backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(error_handler)

        # Debug log file handler (if enabled)
        if self.config.enable_debug_log:
            debug_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / self.config.debug_log_file,
                maxBytes=self.config.max_file_size_mb * 1024 * 1024,
                backupCount=self.config.backup_count,
                encoding="utf-8",
            )
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(detailed_formatter)
            self.logger.addHandler(debug_handler)

        # Console handler (if enabled)
        if self.config.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(standard_formatter)
            self.logger.addHandler(console_handler)

    def log_configuration_loaded(
        self, config_path: str, config_data: dict[str, Any]
    ) -> None:
        """Log configuration loading event."""
        self.logger.info(f"Configuration loaded from: {config_path}")
        self.logger.debug(f"Configuration data: {json.dumps(config_data, indent=2)}")

    def log_model_selection(
        self, model_name: str, model_config: dict[str, Any]
    ) -> None:
        """Log model selection event."""
        self.logger.info(f"Model selected: {model_name}")
        self.logger.debug(f"Model configuration: {json.dumps(model_config, indent=2)}")

    def log_api_call_start(self, model: str, prompt_length: int) -> None:
        """Log the start of an API call."""
        self.logger.info(
            f"API call started - Model: {model}, Prompt length: {prompt_length}"
        )
        self.logger.debug(f"API call correlation ID: {self.correlation_id}")

    def log_api_call_success(
        self, model: str, response_length: int, duration: float
    ) -> None:
        """Log successful API call."""
        self.logger.info(
            f"API call successful - Model: {model}, Response length: {response_length}, Duration: {duration:.2f}s"
        )
        self.logger.debug(f"API call completed - Correlation ID: {self.correlation_id}")

    def log_api_call_error(self, model: str, error: str, duration: float) -> None:
        """Log API call error."""
        self.logger.error(
            f"API call failed - Model: {model}, Error: {error}, Duration: {duration:.2f}s"
        )
        self.logger.debug(f"API call error - Correlation ID: {self.correlation_id}")

    def log_file_generation(
        self, file_name: str, file_path: str, code_length: int
    ) -> None:
        """Log file generation event."""
        self.logger.info(
            f"File generated: {file_name} -> {file_path} ({code_length} characters)"
        )
        self.logger.debug(f"File generation - Correlation ID: {self.correlation_id}")

    def log_file_save(
        self, file_path: str, success: bool, error: str | None = None
    ) -> None:
        """Log file save event."""
        if success:
            self.logger.info(f"File saved successfully: {file_path}")
        else:
            self.logger.error(f"File save failed: {file_path}, Error: {error}")
        self.logger.debug(f"File save - Correlation ID: {self.correlation_id}")

    def log_validation_error(self, field: str, value: Any, error: str) -> None:
        """Log validation errors."""
        self.logger.warning(
            f"Validation error - Field: {field}, Value: {value}, Error: {error}"
        )
        self.logger.debug(f"Validation error - Correlation ID: {self.correlation_id}")

    def log_performance_metric(
        self, operation: str, duration: float, details: dict[str, Any] | None = None
    ):
        """Log performance metrics."""
        self.logger.info(f"Performance - {operation}: {duration:.3f}s")
        if details:
            self.logger.debug(
                f"Performance details - {operation}: {json.dumps(details, indent=2)}"
            )

    def log_user_action(
        self, action: str, parameters: dict[str, Any] | None = None
    ) -> None:
        """Log user actions."""
        self.logger.info(f"User action: {action}")
        if parameters:
            self.logger.debug(
                f"User action parameters: {json.dumps(parameters, indent=2)}"
            )

    def log_system_event(
        self, event: str, details: dict[str, Any] | None = None
    ) -> None:
        """Log system events."""
        self.logger.info(f"System event: {event}")
        if details:
            self.logger.debug(f"System event details: {json.dumps(details, indent=2)}")

    def log_error(self, error: Exception, context: str | None = None) -> None:
        """Log errors with full stack trace."""
        error_msg = f"Error: {str(error)}"
        if context:
            error_msg = f"{context} - {error_msg}"

        self.logger.error(error_msg, exc_info=True)
        self.logger.debug(f"Error correlation ID: {self.correlation_id}")

    def log_warning(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Log warnings."""
        self.logger.warning(message)
        if details:
            self.logger.debug(f"Warning details: {json.dumps(details, indent=2)}")

    def log_info(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Log informational messages."""
        self.logger.info(message)
        if details:
            self.logger.debug(f"Info details: {json.dumps(details, indent=2)}")

    def log_debug(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Log debug messages."""
        self.logger.debug(message)
        if details:
            self.logger.debug(f"Debug details: {json.dumps(details, indent=2)}")

    def get_correlation_id(self) -> str:
        """Get the current correlation ID."""
        return self.correlation_id

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set a new correlation ID."""
        self.correlation_id = correlation_id
        self.logger.debug(f"Correlation ID updated: {correlation_id}")

    def _is_help_mode(self) -> bool:
        """Check if we're in help mode (--help flag present)."""
        import sys

        return "--help" in sys.argv or "-h" in sys.argv


# Global logger instance
_global_logger: O3Logger | None = None


def get_logger() -> O3Logger:
    """Get the global logger instance."""
    global _global_logger
    if _global_logger is None:
        raise RuntimeError("Logger not initialized. Call setup_logger() first.")
    return _global_logger


def setup_logger(config: LogConfig) -> O3Logger:
    """Setup the global logger instance."""
    global _global_logger
    _global_logger = O3Logger(config)
    return _global_logger


def log_performance(operation: str):
    """Decorator to log performance of functions."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger()
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.log_performance_metric(operation, duration)
                return result
            except Exception:
                duration = time.time() - start_time
                logger.log_performance_metric(f"{operation}_error", duration)
                raise

        return wrapper

    return decorator
