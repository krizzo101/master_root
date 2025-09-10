"""
Concrete TokenProvider implementation wrapping existing EnhancedTokenPool
"""

import asyncio
import logging
from typing import Dict, List, Optional

from ..interfaces.token_provider import ITokenProvider
from ..token_pool_enhanced import EnhancedTokenPool

logger = logging.getLogger(__name__)


class TokenProviderImpl(ITokenProvider):
    """
    Concrete implementation of ITokenProvider interface.
    Wraps the existing EnhancedTokenPool to provide dependency injection.
    """

    def __init__(
        self,
        tokens: Optional[List[str]] = None,
        default_reservation_timeout: float = 30.0,
        enable_metrics: bool = True,
    ):
        """
        Initialize the token provider.

        Args:
            tokens: Optional list of API tokens
            default_reservation_timeout: Default timeout for token reservations
            enable_metrics: Enable metrics collection
        """
        self._pool = EnhancedTokenPool(
            tokens=tokens,
            default_reservation_timeout=default_reservation_timeout,
            enable_metrics=enable_metrics,
        )
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure the pool is initialized"""
        if not self._initialized:
            await self._pool.initialize()
            self._initialized = True

    async def acquire_token(
        self, task_id: Optional[str] = None, timeout: float = 30.0
    ) -> str:
        """
        Acquire a single token for use.

        Args:
            task_id: Optional task identifier for tracking
            timeout: Maximum time to wait for token availability

        Returns:
            API token string

        Raises:
            TimeoutError: If token cannot be acquired within timeout
            RuntimeError: If no tokens are available
        """
        await self._ensure_initialized()

        try:
            token = await asyncio.wait_for(
                self._pool.acquire_token(task_id=task_id), timeout=timeout
            )

            if not token:
                raise RuntimeError("No tokens available in pool")

            logger.debug(f"Acquired token for task {task_id}")
            return token

        except asyncio.TimeoutError:
            raise TimeoutError(f"Failed to acquire token within {timeout} seconds")
        except Exception as e:
            logger.error(f"Error acquiring token: {e}")
            raise

    async def release_token(self, token: str, task_id: Optional[str] = None) -> None:
        """
        Release a token back to the pool.

        Args:
            token: Token to release
            task_id: Optional task identifier
        """
        await self._ensure_initialized()

        try:
            await self._pool.release_token(token, task_id=task_id)
            logger.debug(f"Released token for task {task_id}")
        except Exception as e:
            logger.error(f"Error releasing token: {e}")
            # Don't re-raise - token release should be best-effort

    async def acquire_batch(
        self, count: int, batch_id: Optional[str] = None, timeout: float = 30.0
    ) -> List[str]:
        """
        Acquire multiple tokens as a batch.

        Args:
            count: Number of tokens to acquire
            batch_id: Optional batch identifier
            timeout: Maximum time to wait

        Returns:
            List of acquired tokens

        Raises:
            TimeoutError: If tokens cannot be acquired within timeout
            ValueError: If count exceeds available tokens
        """
        await self._ensure_initialized()

        if count > self.get_total_count():
            raise ValueError(
                f"Requested {count} tokens but only {self.get_total_count()} available"
            )

        try:
            tokens = await asyncio.wait_for(
                self._pool.acquire_batch(count, batch_id=batch_id), timeout=timeout
            )

            logger.debug(f"Acquired batch of {len(tokens)} tokens for {batch_id}")
            return tokens

        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Failed to acquire {count} tokens within {timeout} seconds"
            )
        except Exception as e:
            logger.error(f"Error acquiring batch: {e}")
            raise

    async def release_batch(
        self, tokens: List[str], batch_id: Optional[str] = None
    ) -> None:
        """
        Release a batch of tokens.

        Args:
            tokens: List of tokens to release
            batch_id: Optional batch identifier
        """
        await self._ensure_initialized()

        try:
            await self._pool.release_batch(tokens, batch_id=batch_id)
            logger.debug(f"Released batch of {len(tokens)} tokens for {batch_id}")
        except Exception as e:
            logger.error(f"Error releasing batch: {e}")
            # Don't re-raise - token release should be best-effort

    def get_available_count(self) -> int:
        """
        Get current number of available tokens.

        Returns:
            Number of available tokens
        """
        if not self._initialized:
            return 0
        return self._pool.get_available_count()

    def get_total_count(self) -> int:
        """
        Get total number of tokens in the pool.

        Returns:
            Total token count
        """
        if not self._initialized and hasattr(self._pool, "tokens"):
            return len(self._pool.tokens)
        return len(self._pool.tokens) if hasattr(self._pool, "tokens") else 0

    async def get_metrics(self) -> Dict:
        """
        Get token usage metrics.

        Returns:
            Dictionary containing usage metrics
        """
        await self._ensure_initialized()

        metrics = {
            "total_tokens": self.get_total_count(),
            "available_tokens": self.get_available_count(),
            "in_use_tokens": self.get_total_count() - self.get_available_count(),
        }

        if hasattr(self._pool, "metrics") and self._pool.metrics:
            pool_metrics = self._pool.metrics
            metrics.update(
                {
                    "total_acquisitions": pool_metrics.total_acquisitions,
                    "total_releases": pool_metrics.total_releases,
                    "total_timeouts": pool_metrics.total_timeouts,
                    "avg_acquisition_time": pool_metrics.avg_acquisition_time,
                    "avg_usage_duration": pool_metrics.avg_usage_duration,
                }
            )

        return metrics

    async def health_check(self) -> bool:
        """
        Check health status of token provider.

        Returns:
            True if healthy, False otherwise
        """
        try:
            await self._ensure_initialized()

            # Check if we have tokens
            if self.get_total_count() == 0:
                logger.warning("Token provider unhealthy: No tokens available")
                return False

            # Check if pool is responsive
            if hasattr(self._pool, "health_check"):
                return await self._pool.health_check()

            # Basic check - can we get metrics?
            metrics = await self.get_metrics()
            return metrics is not None

        except Exception as e:
            logger.error(f"Token provider health check failed: {e}")
            return False
