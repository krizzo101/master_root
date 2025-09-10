"""
Error handling and retry logic for HECATON orchestration.
Added by Agent-2 during Phase 1 self-amplification.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base


class ErrorHandler:
    """Handles errors and implements retry logic for orchestration."""

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.error_history: Dict[str, list] = {}

    async def execute_with_retry(
        self, func: Callable[..., T], *args, task_id: Optional[str] = None, **kwargs
    ) -> T:
        """
        Execute a function with automatic retry on failure.

        Args:
            func: The async function to execute
            task_id: Optional identifier for tracking
            *args, **kwargs: Arguments to pass to the function

        Returns:
            The result of the function

        Raises:
            The last exception if all retries fail
        """
        last_exception = None
        task_id = task_id or f"task_{datetime.now().timestamp()}"

        for attempt in range(self.config.max_retries):
            try:
                logger.info(f"Executing {task_id}, attempt {attempt + 1}/{self.config.max_retries}")

                # Execute the function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                logger.info(f"Successfully executed {task_id} on attempt {attempt + 1}")
                return result

            except Exception as e:
                last_exception = e

                # Log the error
                logger.warning(f"Attempt {attempt + 1} failed for {task_id}: {str(e)}")

                # Track error history
                if task_id not in self.error_history:
                    self.error_history[task_id] = []
                self.error_history[task_id].append(
                    {
                        "attempt": attempt + 1,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                # If this was the last attempt, raise the exception
                if attempt == self.config.max_retries - 1:
                    logger.error(f"All retries exhausted for {task_id}")
                    raise

                # Calculate delay with exponential backoff
                delay = min(
                    self.config.base_delay * (self.config.exponential_base**attempt),
                    self.config.max_delay,
                )

                logger.info(f"Waiting {delay:.1f}s before retry...")
                await asyncio.sleep(delay)

        # Should never reach here, but just in case
        if last_exception:
            raise last_exception
        raise RuntimeError(f"Unexpected retry logic error for {task_id}")

    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of all errors encountered."""
        return {
            "total_tasks": len(self.error_history),
            "total_errors": sum(len(errors) for errors in self.error_history.values()),
            "error_history": self.error_history,
        }

    async def handle_agent_failure(
        self, agent_id: str, error: Exception, cleanup_func: Optional[Callable] = None
    ):
        """
        Handle agent failure with cleanup.

        Args:
            agent_id: The agent that failed
            error: The exception that occurred
            cleanup_func: Optional cleanup function to call
        """
        logger.error(f"Agent {agent_id} failed: {error}")

        # Perform cleanup if provided
        if cleanup_func:
            try:
                if asyncio.iscoroutinefunction(cleanup_func):
                    await cleanup_func()
                else:
                    cleanup_func()
                logger.info(f"Cleanup completed for agent {agent_id}")
            except Exception as cleanup_error:
                logger.error(f"Cleanup failed for agent {agent_id}: {cleanup_error}")

        # Record the failure
        if agent_id not in self.error_history:
            self.error_history[agent_id] = []
        self.error_history[agent_id].append(
            {"error": str(error), "timestamp": datetime.now().isoformat(), "type": "agent_failure"}
        )


# Global error handler instance
error_handler = ErrorHandler()


async def safe_execute(func: Callable, *args, **kwargs):
    """Convenience function for safe execution with retry."""
    return await error_handler.execute_with_retry(func, *args, **kwargs)
