"""
DRY Logging Manager - Centralized Logging Configuration

Eliminates the duplication of `logger = logging.getLogger(__name__)` 
found in 40+ files across the codebase.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Dict, Optional, Union
from datetime import datetime
import json


class LoggingManager:
    """
    Centralized logging manager eliminating logging setup duplication.

    Eliminates duplication of:
    - Logger creation patterns
    - Formatter configuration
    - Handler setup
    - Log level management
    - File rotation configuration
    """

    _instance: Optional["LoggingManager"] = None
    _loggers: Dict[str, logging.Logger] = {}
    _configured = False

    def __new__(cls) -> "LoggingManager":
        """Singleton pattern for global logging management."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._configured:
            self._setup_default_configuration()
            self._configured = True

    def _setup_default_configuration(self):
        """Setup default logging configuration."""
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "asea_orchestrator.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    def get_logger(
        self, name: str, level: Optional[Union[str, int]] = None
    ) -> logging.Logger:
        """
        Get or create a logger with standardized configuration.

        Args:
            name: Logger name (usually __name__)
            level: Optional logging level override

        Returns:
            Configured logger instance
        """
        if name in self._loggers:
            return self._loggers[name]

        logger = logging.getLogger(name)

        if level:
            if isinstance(level, str):
                level = getattr(logging, level.upper())
            logger.setLevel(level)

        self._loggers[name] = logger
        return logger

    def configure_plugin_logger(
        self, plugin_name: str, log_to_separate_file: bool = False
    ) -> logging.Logger:
        """
        Configure logger specifically for a plugin.

        Args:
            plugin_name: Name of the plugin
            log_to_separate_file: Whether to create separate log file for plugin

        Returns:
            Configured plugin logger
        """
        logger_name = f"asea.plugins.{plugin_name}"
        logger = self.get_logger(logger_name)

        if log_to_separate_file:
            log_dir = Path("logs/plugins")
            log_dir.mkdir(parents=True, exist_ok=True)

            # Create plugin-specific file handler
            plugin_handler = logging.handlers.RotatingFileHandler(
                log_dir / f"{plugin_name}.log",
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=3,
            )
            plugin_handler.setLevel(logging.DEBUG)
            plugin_formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
            )
            plugin_handler.setFormatter(plugin_formatter)
            logger.addHandler(plugin_handler)

        return logger

    def configure_database_logger(self, client_name: str) -> logging.Logger:
        """
        Configure logger specifically for database clients.

        Args:
            client_name: Name of the database client

        Returns:
            Configured database logger
        """
        logger_name = f"asea.database.{client_name}"
        logger = self.get_logger(logger_name)

        # Database operations might be verbose, so allow level override
        log_level = logging.INFO  # Default to INFO for database operations
        logger.setLevel(log_level)

        return logger

    def set_global_level(self, level: Union[str, int]) -> None:
        """
        Set logging level for all loggers.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if isinstance(level, str):
            level = getattr(logging, level.upper())

        # Update root logger
        logging.getLogger().setLevel(level)

        # Update all managed loggers
        for logger in self._loggers.values():
            logger.setLevel(level)

    def add_structured_logging(self, enable: bool = True) -> None:
        """
        Enable structured JSON logging for better log analysis.

        Args:
            enable: Whether to enable structured logging
        """
        if not enable:
            return

        class StructuredFormatter(logging.Formatter):
            """JSON formatter for structured logging."""

            def format(self, record: logging.LogRecord) -> str:
                log_data = {
                    "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno,
                }

                # Add exception info if present
                if record.exc_info:
                    log_data["exception"] = self.formatException(record.exc_info)

                # Add extra fields if present
                if hasattr(record, "extra_data"):
                    log_data.update(record.extra_data)

                return json.dumps(log_data)

        # Add structured handler
        log_dir = Path("logs")
        structured_handler = logging.handlers.RotatingFileHandler(
            log_dir / "structured.jsonl",
            maxBytes=20 * 1024 * 1024,  # 20MB
            backupCount=5,
        )
        structured_handler.setLevel(logging.INFO)
        structured_handler.setFormatter(StructuredFormatter())

        logging.getLogger().addHandler(structured_handler)

    def log_performance_metric(
        self, logger: logging.Logger, operation: str, duration: float, **extra_data
    ):
        """
        Log performance metrics in a standardized format.

        Args:
            logger: Logger instance
            operation: Name of the operation
            duration: Duration in seconds
            extra_data: Additional metadata
        """
        metric_data = {
            "metric_type": "performance",
            "operation": operation,
            "duration_seconds": duration,
            **extra_data,
        }

        # Create log record with extra data
        record = logger.makeRecord(
            logger.name,
            logging.INFO,
            "",
            0,
            f"Performance: {operation} completed in {duration:.3f}s",
            (),
            None,
        )
        record.extra_data = metric_data
        logger.handle(record)

    def log_plugin_event(self, plugin_name: str, event_type: str, **event_data):
        """
        Log plugin events in a standardized format.

        Args:
            plugin_name: Name of the plugin
            event_type: Type of event (execution, error, etc.)
            event_data: Event metadata
        """
        logger = self.get_logger(f"asea.plugins.{plugin_name}")

        event_record = {
            "event_type": "plugin_event",
            "plugin_name": plugin_name,
            "event_category": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            **event_data,
        }

        record = logger.makeRecord(
            logger.name,
            logging.INFO,
            "",
            0,
            f"Plugin {plugin_name}: {event_type}",
            (),
            None,
        )
        record.extra_data = event_record
        logger.handle(record)


# Global instance for easy access
_logging_manager = LoggingManager()


def get_logger(name: str, level: Optional[Union[str, int]] = None) -> logging.Logger:
    """
    Get a standardized logger instance.

    This is the DRY replacement for `logger = logging.getLogger(__name__)`

    Args:
        name: Logger name (usually __name__)
        level: Optional logging level override

    Returns:
        Configured logger instance
    """
    return _logging_manager.get_logger(name, level)


def get_plugin_logger(plugin_name: str, separate_file: bool = False) -> logging.Logger:
    """
    Get a logger configured specifically for a plugin.

    Args:
        plugin_name: Name of the plugin
        separate_file: Whether to create separate log file

    Returns:
        Plugin-specific logger
    """
    return _logging_manager.configure_plugin_logger(plugin_name, separate_file)


def get_database_logger(client_name: str) -> logging.Logger:
    """
    Get a logger configured specifically for database operations.

    Args:
        client_name: Name of the database client

    Returns:
        Database-specific logger
    """
    return _logging_manager.configure_database_logger(client_name)


def configure_logging(
    level: Union[str, int] = "INFO",
    structured: bool = False,
    plugin_separate_files: bool = False,
) -> None:
    """
    Configure global logging settings.

    Args:
        level: Global logging level
        structured: Enable structured JSON logging
        plugin_separate_files: Create separate files for plugins
    """
    _logging_manager.set_global_level(level)

    if structured:
        _logging_manager.add_structured_logging(True)


def log_performance(
    logger: logging.Logger, operation: str, duration: float, **extra_data
):
    """
    Log performance metrics in standardized format.

    Args:
        logger: Logger instance
        operation: Operation name
        duration: Duration in seconds
        extra_data: Additional metadata
    """
    _logging_manager.log_performance_metric(logger, operation, duration, **extra_data)


def log_plugin_event(plugin_name: str, event_type: str, **event_data):
    """
    Log plugin events in standardized format.

    Args:
        plugin_name: Plugin name
        event_type: Event type
        event_data: Event metadata
    """
    _logging_manager.log_plugin_event(plugin_name, event_type, **event_data)


# Backwards compatibility aliases
def getLogger(name: str) -> logging.Logger:
    """Backwards compatible alias for get_logger."""
    return get_logger(name)
