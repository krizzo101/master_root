"""
Mock TokenProvider implementation for testing
"""

import asyncio
from collections import deque
from typing import Dict, List, Optional, Set

from ..interfaces.token_provider import ITokenProvider


class MockTokenProvider(ITokenProvider):
    """
    Mock implementation of ITokenProvider for testing.
    Simulates token management without real API tokens.
    """

    def __init__(
        self,
        initial_tokens: Optional[List[str]] = None,
        simulate_delays: bool = False,
        failure_rate: float = 0.0,
    ):
        """
        Initialize mock token provider.

        Args:
            initial_tokens: Initial mock tokens (generates if None)
            simulate_delays: Add realistic delays to operations
            failure_rate: Probability of operations failing (0.0-1.0)
        """
        self.tokens = initial_tokens or [f"mock_token_{i}" for i in range(10)]
        self.available_tokens = deque(self.tokens.copy())
        self.in_use_tokens: Set[str] = set()
        self.simulate_delays = simulate_delays
        self.failure_rate = failure_rate

        # Tracking for assertions
        self.acquisition_count = 0
        self.release_count = 0
        self.batch_acquisition_count = 0
        self.batch_release_count = 0
        self.acquisition_history: List[Dict] = []
        self.release_history: List[Dict] = []

    async def _maybe_fail(self):
        """Simulate random failures for testing error handling"""
        import random

        if random.random() < self.failure_rate:
            raise RuntimeError("Simulated token provider failure")

    async def _maybe_delay(self, min_ms: int = 10, max_ms: int = 50):
        """Add realistic delays if configured"""
        if self.simulate_delays:
            import random

            delay = random.randint(min_ms, max_ms) / 1000
            await asyncio.sleep(delay)

    async def acquire_token(
        self, task_id: Optional[str] = None, timeout: float = 30.0
    ) -> str:
        """Acquire a mock token"""
        await self._maybe_delay()
        await self._maybe_fail()

        if not self.available_tokens:
            # Wait for token to become available
            start_time = asyncio.get_event_loop().time()
            while not self.available_tokens:
                if asyncio.get_event_loop().time() - start_time > timeout:
                    raise TimeoutError(f"No tokens available within {timeout} seconds")
                await asyncio.sleep(0.1)

        token = self.available_tokens.popleft()
        self.in_use_tokens.add(token)
        self.acquisition_count += 1

        self.acquisition_history.append(
            {
                "token": token,
                "task_id": task_id,
                "type": "single",
            }
        )

        return token

    async def release_token(self, token: str, task_id: Optional[str] = None) -> None:
        """Release a mock token"""
        await self._maybe_delay(5, 20)

        if token in self.in_use_tokens:
            self.in_use_tokens.remove(token)
            self.available_tokens.append(token)
            self.release_count += 1

            self.release_history.append(
                {
                    "token": token,
                    "task_id": task_id,
                    "type": "single",
                }
            )

    async def acquire_batch(
        self, count: int, batch_id: Optional[str] = None, timeout: float = 30.0
    ) -> List[str]:
        """Acquire multiple mock tokens"""
        await self._maybe_delay(20, 100)
        await self._maybe_fail()

        if count > len(self.tokens):
            raise ValueError(
                f"Requested {count} tokens but only {len(self.tokens)} available"
            )

        # Wait for enough tokens
        start_time = asyncio.get_event_loop().time()
        while len(self.available_tokens) < count:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(
                    f"Could not acquire {count} tokens within {timeout} seconds"
                )
            await asyncio.sleep(0.1)

        acquired = []
        for _ in range(count):
            token = self.available_tokens.popleft()
            self.in_use_tokens.add(token)
            acquired.append(token)

        self.batch_acquisition_count += 1
        self.acquisition_history.append(
            {
                "tokens": acquired,
                "batch_id": batch_id,
                "type": "batch",
                "count": count,
            }
        )

        return acquired

    async def release_batch(
        self, tokens: List[str], batch_id: Optional[str] = None
    ) -> None:
        """Release multiple mock tokens"""
        await self._maybe_delay(10, 50)

        for token in tokens:
            if token in self.in_use_tokens:
                self.in_use_tokens.remove(token)
                self.available_tokens.append(token)

        self.batch_release_count += 1
        self.release_history.append(
            {
                "tokens": tokens,
                "batch_id": batch_id,
                "type": "batch",
                "count": len(tokens),
            }
        )

    def get_available_count(self) -> int:
        """Get number of available mock tokens"""
        return len(self.available_tokens)

    def get_total_count(self) -> int:
        """Get total number of mock tokens"""
        return len(self.tokens)

    async def get_metrics(self) -> Dict:
        """Get mock metrics for testing"""
        await self._maybe_delay(5, 15)

        return {
            "total_tokens": self.get_total_count(),
            "available_tokens": self.get_available_count(),
            "in_use_tokens": len(self.in_use_tokens),
            "total_acquisitions": self.acquisition_count,
            "total_releases": self.release_count,
            "batch_acquisitions": self.batch_acquisition_count,
            "batch_releases": self.batch_release_count,
            "acquisition_history_size": len(self.acquisition_history),
            "release_history_size": len(self.release_history),
            "simulated_delays": self.simulate_delays,
            "failure_rate": self.failure_rate,
        }

    async def health_check(self) -> bool:
        """Mock health check"""
        await self._maybe_delay(5, 10)

        # Simulate unhealthy state if no tokens or high failure rate
        if not self.tokens:
            return False
        if self.failure_rate > 0.5:
            return False

        return True

    # Testing utility methods

    def reset(self):
        """Reset mock to initial state for testing"""
        self.available_tokens = deque(self.tokens.copy())
        self.in_use_tokens.clear()
        self.acquisition_count = 0
        self.release_count = 0
        self.batch_acquisition_count = 0
        self.batch_release_count = 0
        self.acquisition_history.clear()
        self.release_history.clear()

    def set_available_tokens(self, tokens: List[str]):
        """Set specific tokens as available for testing"""
        self.available_tokens = deque(tokens)
        self.in_use_tokens = set(t for t in self.tokens if t not in tokens)

    def get_acquisition_history(self) -> List[Dict]:
        """Get history of token acquisitions for assertions"""
        return self.acquisition_history.copy()

    def get_release_history(self) -> List[Dict]:
        """Get history of token releases for assertions"""
        return self.release_history.copy()
