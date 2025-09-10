"""
Token Provider Interface for dependency injection
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class ITokenProvider(ABC):
    """
    Abstract interface for token providers.
    Defines contract for acquiring and releasing API tokens.
    """

    @abstractmethod
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
        pass

    @abstractmethod
    async def release_token(self, token: str, task_id: Optional[str] = None) -> None:
        """
        Release a token back to the pool.

        Args:
            token: Token to release
            task_id: Optional task identifier
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def release_batch(
        self, tokens: List[str], batch_id: Optional[str] = None
    ) -> None:
        """
        Release a batch of tokens.

        Args:
            tokens: List of tokens to release
            batch_id: Optional batch identifier
        """
        pass

    @abstractmethod
    def get_available_count(self) -> int:
        """
        Get current number of available tokens.

        Returns:
            Number of available tokens
        """
        pass

    @abstractmethod
    def get_total_count(self) -> int:
        """
        Get total number of tokens in the pool.

        Returns:
            Total token count
        """
        pass

    @abstractmethod
    async def get_metrics(self) -> Dict:
        """
        Get token usage metrics.

        Returns:
            Dictionary containing usage metrics
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check health status of token provider.

        Returns:
            True if healthy, False otherwise
        """
        pass
