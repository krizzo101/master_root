"""Utility functions for opsvi-orchestration.

Utility functions for opsvi-orchestration
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps
import time

logger = logging.getLogger(__name__)

# Async utilities
async def safe_async_call(
    func: Callable,
    *args: Any,
    **kwargs: Any
) -> Any:
    """Safely call an async function with error handling.

    Args:
        func: Function to call
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Function result

    Raises:
        Exception: If function call fails
    """
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Async call failed: {e}")
        raise

def retry_async(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0
) -> Callable:
    """Decorator for async retry logic.

    Args:
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        backoff: Backoff multiplier

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1} failed, retrying in {current_delay}s: {e}"
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed")

            raise last_exception
        return wrapper
    return decorator

# Configuration utilities
def merge_configs(
    base: Dict[str, Any],
    override: Dict[str, Any]
) -> Dict[str, Any]:
    """Merge configuration dictionaries.

    Args:
        base: Base configuration
        override: Override configuration

    Returns:
        Merged configuration
    """
    result = base.copy()
    result.update(override)
    return result

def validate_config(
    config: Dict[str, Any],
    required_keys: List[str]
) -> None:
    """Validate configuration has required keys.

    Args:
        config: Configuration to validate
        required_keys: Required configuration keys

    Raises:
        ValueError: If required keys are missing
    """
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ValueError(f"Missing required configuration keys: {missing_keys}")

# Performance utilities
def timing_decorator(func: Callable) -> Callable:
    """Decorator to time function execution.

    Args:
        func: Function to time

    Returns:
        Decorated function
    """
    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            logger.debug(f"{func.__name__} took {end_time - start_time:.4f}s")

    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            logger.debug(f"{func.__name__} took {end_time - start_time:.4f}s")

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

# Library-specific utilities

