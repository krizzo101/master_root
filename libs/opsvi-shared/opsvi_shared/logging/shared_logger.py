"""
shared_logger.py

A reusable logging interface for Python projects, supporting multiple log levels, flexible configuration, and log rotation.
Compatible with Python's built-in logging module. Follows PEP 8 and industry best practices.
"""

import logging
import logging.handlers
from typing import Any, Dict, Optional


class SharedLogger:
    """
    SharedLogger provides a reusable, configurable logging interface for Python applications.
    Supports multiple log levels, console/file handlers, and log rotation.
    """

    _instance: Optional["SharedLogger"] = None

    def __new__(cls, *args, **kwargs) -> "SharedLogger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        name: str = "shared_logger",
        level: int = logging.INFO,
        fmt: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt: str = "%Y-%m-%d %H:%M:%S",
        log_to_console: bool = True,
        log_to_file: bool = False,
        log_file: str = "app.log",
        rotation: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize the shared logger.

        Args:
            name: Logger name.
            level: Logging level (e.g., logging.INFO).
            fmt: Log message format.
            datefmt: Date/time format for log messages.
            log_to_console: Enable console logging.
            log_to_file: Enable file logging.
            log_file: File path for log output.
            rotation: Log rotation config (e.g., {"maxBytes": 1048576, "backupCount": 3} or {"when": "midnight", "backupCount": 7}).
        """
        if hasattr(self, "_initialized") and self._initialized:
            return
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False
        formatter = logging.Formatter(fmt, datefmt)
        self.logger.handlers.clear()
        if log_to_console:
            ch = logging.StreamHandler()
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
        if log_to_file:
            if rotation:
                if "maxBytes" in rotation:
                    fh = logging.handlers.RotatingFileHandler(
                        log_file,
                        maxBytes=rotation.get("maxBytes", 1048576),
                        backupCount=rotation.get("backupCount", 3),
                        encoding="utf-8",
                    )
                elif "when" in rotation:
                    fh = logging.handlers.TimedRotatingFileHandler(
                        log_file,
                        when=rotation.get("when", "midnight"),
                        interval=rotation.get("interval", 1),
                        backupCount=rotation.get("backupCount", 7),
                        encoding="utf-8",
                    )
                else:
                    raise ValueError(
                        "Invalid rotation config. Use 'maxBytes' or 'when'."
                    )
            else:
                fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
        self._initialized = True

    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log a message with DEBUG level."""
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        """Log a message with INFO level."""
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log a message with WARNING level."""
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        """Log a message with ERROR level."""
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        """Log a message with CRITICAL level."""
        self.logger.critical(msg, *args, **kwargs)

    def get_logger(self) -> logging.Logger:
        """
        Get the underlying logging.Logger instance.
        Returns:
            logging.Logger: The logger instance.
        """
        return self.logger


# Usage Examples
if __name__ == "__main__":
    # Basic console logger
    logger = SharedLogger(level=logging.DEBUG)
    logger.info("This is an info message.")
    logger.debug("This is a debug message.")
    logger.warning("This is a warning.")
    logger.error("This is an error.")
    logger.critical("This is critical.")

    # File logger with rotation (by size)
    file_logger = SharedLogger(
        name="file_logger",
        level=logging.INFO,
        log_to_console=False,
        log_to_file=True,
        log_file="my_app.log",
        rotation={"maxBytes": 1024 * 1024, "backupCount": 5},
    )
    file_logger.info("This will go to a rotating file handler.")

    # File logger with rotation (by time)
    timed_logger = SharedLogger(
        name="timed_logger",
        level=logging.INFO,
        log_to_console=False,
        log_to_file=True,
        log_file="timed_app.log",
        rotation={"when": "midnight", "backupCount": 7},
    )
    timed_logger.info("This will go to a timed rotating file handler.")
