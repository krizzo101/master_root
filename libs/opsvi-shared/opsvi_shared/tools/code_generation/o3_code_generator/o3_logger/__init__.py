"""
O3 Logger package for O3 Code Generator.

This package provides comprehensive logging functionality including:
- Standard application logging
- Debug logging with detailed information
- Error logging with stack traces
- Performance logging and metrics
- Structured logging with correlation IDs
"""

from .logger import LogConfig, O3Logger, get_logger, setup_logger

__all__ = ["O3Logger", "get_logger", "setup_logger", "LogConfig"]
