"""
Debug Logger for HECATON
Comprehensive logging with toggleable debug mode
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Global debug flag - can be set via environment or directly
DEBUG_MODE = os.environ.get("HECATON_DEBUG", "true").lower() == "true"


class DebugLogger:
    """Enhanced logger with debug capabilities for HECATON"""

    def __init__(self, name: str, debug: Optional[bool] = None):
        """
        Initialize logger with debug capabilities

        Args:
            name: Logger name (usually module name)
            debug: Override global debug setting (None uses global)
        """
        self.logger = logging.getLogger(name)
        self.name = name
        self.debug = debug if debug is not None else DEBUG_MODE

        # Setup logging
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging with file and console handlers"""

        # Set level based on debug mode
        level = logging.DEBUG if self.debug else logging.INFO
        self.logger.setLevel(level)

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Console handler with color coding
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # Detailed format for debug mode
        if self.debug:
            format_str = (
                "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | "
                "%(message)s"
            )
        else:
            format_str = "%(asctime)s | %(levelname)-8s | %(message)s"

        console_formatter = logging.Formatter(format_str, datefmt="%H:%M:%S")
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler for debug mode
        if self.debug:
            log_dir = Path("/home/opsvi/master_root/apps/hecaton/logs")
            log_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"hecaton_debug_{timestamp}.log"

            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)

            file_format = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | "
                "%(message)s | PID:%(process)d | Thread:%(thread)d",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)

            print(f"📝 Debug log: {log_file}")

    def debug_enter(self, func_name: str, **kwargs):
        """Log function entry with parameters"""
        if self.debug:
            params = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            self.logger.debug(f"→ ENTER {func_name}({params})")

    def debug_exit(self, func_name: str, result: Any = None):
        """Log function exit with result"""
        if self.debug:
            self.logger.debug(f"← EXIT {func_name} with result: {result}")

    def debug_step(self, step: str, details: Any = None):
        """Log a debug step with optional details"""
        if self.debug:
            if details:
                self.logger.debug(f"  STEP: {step} | Details: {details}")
            else:
                self.logger.debug(f"  STEP: {step}")

    def debug_data(self, label: str, data: Any):
        """Log data structure for inspection"""
        if self.debug:
            self.logger.debug(f"  DATA[{label}]: {data}")

    def debug_error(self, error: Exception, context: str = ""):
        """Log error with full details"""
        if self.debug:
            import traceback

            tb = traceback.format_exc()
            self.logger.error(f"  ERROR in {context}: {error}\n{tb}")
        else:
            self.logger.error(f"Error: {error}")

    # Standard logging methods with debug awareness
    def info(self, msg: str, **kwargs):
        """Info level log"""
        if kwargs and self.debug:
            msg = f"{msg} | {kwargs}"
        self.logger.info(msg)

    def warning(self, msg: str, **kwargs):
        """Warning level log"""
        if kwargs and self.debug:
            msg = f"{msg} | {kwargs}"
        self.logger.warning(msg)

    def error(self, msg: str, **kwargs):
        """Error level log"""
        if kwargs and self.debug:
            msg = f"{msg} | {kwargs}"
        self.logger.error(msg)

    def critical(self, msg: str, **kwargs):
        """Critical level log"""
        if kwargs and self.debug:
            msg = f"{msg} | {kwargs}"
        self.logger.critical(msg)


def get_logger(name: str) -> DebugLogger:
    """Get a debug logger instance"""
    return DebugLogger(name)


def set_debug_mode(enabled: bool):
    """Set global debug mode"""
    global DEBUG_MODE
    DEBUG_MODE = enabled
    os.environ["HECATON_DEBUG"] = "true" if enabled else "false"
    print(f"🔧 Debug mode: {'ENABLED' if enabled else 'DISABLED'}")


def is_debug_mode() -> bool:
    """Check if debug mode is enabled"""
    return DEBUG_MODE
