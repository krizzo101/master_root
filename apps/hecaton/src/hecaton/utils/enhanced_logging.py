"""
Enhanced logging utilities for HECATON with detailed context
"""

import logging
import sys
import time
from functools import wraps
from typing import Any, Dict, Optional


# Color codes for terminal output
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"


class ContextualFormatter(logging.Formatter):
    """Custom formatter with colors and context"""

    COLORS = {
        "DEBUG": Colors.CYAN,
        "INFO": Colors.GREEN,
        "WARNING": Colors.YELLOW,
        "ERROR": Colors.RED,
        "CRITICAL": Colors.RED + Colors.BOLD,
    }

    EMOJIS = {
        "DEBUG": "🔍",
        "INFO": "📝",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "💥",
    }

    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if sys.stdout.isatty():  # Only color if terminal
            color = self.COLORS.get(levelname, "")
            record.levelname = f"{color}{levelname:8s}{Colors.RESET}"

        # Add emoji
        emoji = self.EMOJIS.get(levelname, "")

        # Format with enhanced context
        record.emoji = emoji
        return super().format(record)


def setup_logger(
    name: str = None,
    level: int = logging.INFO,
    add_file: bool = False,
    file_path: str = "hecaton.log",
) -> logging.Logger:
    """
    Set up a logger with enhanced formatting.

    Args:
        name: Logger name (defaults to root logger)
        level: Logging level
        add_file: Whether to add file handler
        file_path: Path for log file

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers = []

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_format = ContextualFormatter(
        "%(asctime)s %(emoji)s [%(levelname)s] %(name)s:%(lineno)d | %(funcName)s() | %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler without colors
    if add_file:
        file_handler = logging.FileHandler(file_path)
        file_format = logging.Formatter(
            "%(asctime)s [%(levelname)8s] %(name)s:%(lineno)d | %(funcName)s() | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


def log_execution_time(func):
    """Decorator to log function execution time"""

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.time()

        # Log function entry with arguments
        arg_str = ", ".join([str(a)[:50] for a in args[:3]])  # First 3 args
        kwarg_str = ", ".join(
            [f"{k}={str(v)[:20]}" for k, v in list(kwargs.items())[:3]]
        )

        logger.debug(
            f"→ Entering {func.__name__}({arg_str}{', ' + kwarg_str if kwarg_str else ''})"
        )

        try:
            result = await func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.debug(
                f"← Exiting {func.__name__} | elapsed={elapsed:.3f}s | success=True"
            )
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"← Exiting {func.__name__} | elapsed={elapsed:.3f}s | error={e}"
            )
            raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.time()

        # Log function entry
        arg_str = ", ".join([str(a)[:50] for a in args[:3]])
        kwarg_str = ", ".join(
            [f"{k}={str(v)[:20]}" for k, v in list(kwargs.items())[:3]]
        )

        logger.debug(
            f"→ Entering {func.__name__}({arg_str}{', ' + kwarg_str if kwarg_str else ''})"
        )

        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.debug(f"← Exiting {func.__name__} | elapsed={elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"← Exiting {func.__name__} | elapsed={elapsed:.3f}s | error={e}"
            )
            raise

    # Return appropriate wrapper
    import asyncio

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def log_loop_iteration(
    logger: logging.Logger,
    loop_name: str,
    iteration: int,
    total: Optional[int] = None,
    **context,
):
    """
    Log loop iteration with context.

    Args:
        logger: Logger instance
        loop_name: Name of the loop
        iteration: Current iteration (1-based)
        total: Total iterations if known
        **context: Additional context to log
    """
    total_str = f"/{total}" if total else ""
    context_str = " | ".join([f"{k}={v}" for k, v in context.items()])

    logger.debug(
        f"Loop [{loop_name}] | iteration={iteration}{total_str} | {context_str}"
    )


def log_state_transition(
    logger: logging.Logger, component: str, old_state: str, new_state: str, **context
):
    """
    Log state transitions.

    Args:
        logger: Logger instance
        component: Component name
        old_state: Previous state
        new_state: New state
        **context: Additional context
    """
    context_str = (
        " | ".join([f"{k}={v}" for k, v in context.items()]) if context else ""
    )
    extra = f" | {context_str}" if context_str else ""

    logger.info(f"State change [{component}] | {old_state} → {new_state}{extra}")


def log_resource_usage(
    logger: logging.Logger, resource_type: str, action: str, resource_id: str, **metrics
):
    """
    Log resource usage (tokens, worktrees, etc).

    Args:
        logger: Logger instance
        resource_type: Type of resource
        action: Action performed (acquire, release, etc)
        resource_id: Resource identifier
        **metrics: Resource metrics
    """
    metrics_str = " | ".join([f"{k}={v}" for k, v in metrics.items()])

    emoji = (
        "🔐" if resource_type == "token" else "📂" if resource_type == "worktree" else "📦"
    )
    logger.debug(
        f"{emoji} Resource [{resource_type}] | action={action} | id={resource_id} | {metrics_str}"
    )


def log_agent_event(logger: logging.Logger, agent_id: str, event: str, **details):
    """
    Log agent-specific events.

    Args:
        logger: Logger instance
        agent_id: Agent identifier
        event: Event type
        **details: Event details
    """
    details_str = " | ".join([f"{k}={v}" for k, v in details.items()])

    emoji_map = {
        "start": "🚀",
        "complete": "✅",
        "fail": "❌",
        "timeout": "⏱️",
        "retry": "🔄",
        "checkpoint": "💾",
    }

    emoji = emoji_map.get(event, "🤖")
    logger.info(f"{emoji} Agent [{agent_id}] | event={event} | {details_str}")


# Singleton logger setup
_main_logger = None


def get_logger(name: str = None) -> logging.Logger:
    """Get or create enhanced logger"""
    global _main_logger

    if _main_logger is None:
        _main_logger = setup_logger("hecaton", level=logging.INFO, add_file=True)
        _main_logger.info("=" * 60)
        _main_logger.info("HECATON Enhanced Logging Initialized")
        _main_logger.info("=" * 60)

    if name:
        return logging.getLogger(name)
    return _main_logger
