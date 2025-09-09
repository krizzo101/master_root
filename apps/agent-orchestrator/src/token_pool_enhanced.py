#!/usr/bin/env python3
"""
Enhanced Token Pool Implementation with Lock-Free Distribution
Eliminates contention through asyncio.Queue and reservation system
"""

import asyncio
import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class TokenState(Enum):
    """Token availability states"""

    AVAILABLE = "available"
    RESERVED = "reserved"
    IN_USE = "in_use"
    EXPIRED = "expired"


@dataclass
class TokenReservation:
    """Represents a token reservation with timeout"""

    reservation_id: str
    token_idx: int
    token: str
    reserved_at: float
    timeout: float
    task_id: Optional[str] = None
    batch_id: Optional[str] = None

    @property
    def is_expired(self) -> bool:
        """Check if reservation has expired"""
        return time.time() - self.reserved_at > self.timeout

    @property
    def time_remaining(self) -> float:
        """Time remaining before expiration"""
        return max(0, self.timeout - (time.time() - self.reserved_at))


@dataclass
class TokenMetrics:
    """Token usage metrics for monitoring"""

    total_acquisitions: int = 0
    total_releases: int = 0
    total_reservations: int = 0
    total_timeouts: int = 0
    total_batch_allocations: int = 0
    acquisition_times: List[float] = field(default_factory=list)
    usage_durations: List[float] = field(default_factory=list)
    queue_depths: List[int] = field(default_factory=list)

    def record_acquisition(self, duration: float):
        """Record token acquisition metrics"""
        self.total_acquisitions += 1
        self.acquisition_times.append(duration)
        # Keep only last 1000 measurements to prevent memory growth
        if len(self.acquisition_times) > 1000:
            self.acquisition_times = self.acquisition_times[-1000:]

    def record_usage(self, duration: float):
        """Record token usage duration"""
        self.usage_durations.append(duration)
        if len(self.usage_durations) > 1000:
            self.usage_durations = self.usage_durations[-1000:]

    @property
    def avg_acquisition_time(self) -> float:
        """Average time to acquire a token"""
        return (
            sum(self.acquisition_times) / len(self.acquisition_times)
            if self.acquisition_times
            else 0
        )

    @property
    def avg_usage_duration(self) -> float:
        """Average token usage duration"""
        return (
            sum(self.usage_durations) / len(self.usage_durations)
            if self.usage_durations
            else 0
        )


class EnhancedTokenPool:
    """
    Lock-free token pool implementation using asyncio.Queue

    Features:
    - Lock-free token distribution via asyncio.Queue
    - Token reservation system with timeout
    - Batch allocation for multi-agent tasks
    - Backward compatibility with original TokenPool interface
    - Comprehensive metrics and monitoring
    """

    def __init__(
        self,
        tokens: List[str] = None,
        default_reservation_timeout: float = 30.0,
        enable_metrics: bool = True,
    ):
        """
        Initialize enhanced token pool

        Args:
            tokens: List of API tokens (loads from environment if None)
            default_reservation_timeout: Default timeout for reservations in seconds
            enable_metrics: Enable metrics collection
        """
        # Load tokens using same strategies as original
        self.tokens = self._load_tokens(tokens)

        if not self.tokens:
            raise RuntimeError(
                "CATASTROPHIC FAILURE: No valid tokens available. "
                "TokenTool must provide tokens or system must fail - NO ENV FALLBACK."
            )

        # Lock-free queue for available tokens
        self.available_queue: asyncio.Queue = asyncio.Queue()

        # Token state tracking (no locks needed for reads)
        self.token_states: Dict[int, TokenState] = {}
        self.reservations: Dict[str, TokenReservation] = {}
        self.token_to_reservation: Dict[int, str] = {}

        # Batch allocation tracking
        self.batch_allocations: Dict[str, List[int]] = defaultdict(list)

        # Configuration
        self.default_reservation_timeout = default_reservation_timeout
        self.enable_metrics = enable_metrics

        # Metrics
        self.metrics = TokenMetrics() if enable_metrics else None

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._initialized = False

        # Backward compatibility
        self.current_index = 0  # For round-robin compatibility
        self.lock = asyncio.Lock()  # Kept for backward compatibility only
        self.in_use: Set[int] = set()  # For backward compatibility

        logger.info(f"Enhanced token pool initialized with {len(self.tokens)} tokens")

    async def initialize(self):
        """Async initialization - must be called before use"""
        if self._initialized:
            return

        # Initialize all tokens as available in the queue
        for idx in range(len(self.tokens)):
            await self.available_queue.put(idx)
            self.token_states[idx] = TokenState.AVAILABLE

        # Start cleanup task for expired reservations
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_reservations())

        self._initialized = True
        logger.info("Token pool async initialization complete")

    async def shutdown(self):
        """Clean shutdown of background tasks"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Token pool shutdown complete")

    def _load_tokens(self, tokens: Optional[List[str]]) -> List[str]:
        """Load tokens using same strategy as original TokenPool"""
        if tokens is not None:
            return [t for t in tokens if t and t.strip()]

        loaded_tokens = []

        # Strategy 1: Try relative import
        try:
            from .token_loader import load_tokens

            loaded_tokens = load_tokens()
            if loaded_tokens:
                logger.info(f"Loaded {len(loaded_tokens)} tokens via relative import")
                return loaded_tokens
        except ImportError:
            pass

        # Strategy 2: Try absolute import
        if not loaded_tokens:
            try:
                import os
                import sys

                orchestrator_src = os.path.join(os.path.dirname(__file__), "..")
                if orchestrator_src not in sys.path:
                    sys.path.insert(0, orchestrator_src)
                from src.token_loader import load_tokens

                loaded_tokens = load_tokens()
                if loaded_tokens:
                    logger.info(
                        f"Loaded {len(loaded_tokens)} tokens via absolute import"
                    )
                    return loaded_tokens
            except ImportError:
                pass

        # Strategy 3: Direct file access
        if not loaded_tokens:
            try:
                import importlib.util
                import os

                token_loader_path = os.path.join(
                    os.path.dirname(__file__), "token_loader.py"
                )
                if os.path.exists(token_loader_path):
                    spec = importlib.util.spec_from_file_location(
                        "token_loader", token_loader_path
                    )
                    token_loader = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(token_loader)
                    loaded_tokens = token_loader.load_tokens()
                    if loaded_tokens:
                        logger.info(
                            f"Loaded {len(loaded_tokens)} tokens via direct file access"
                        )
                        return loaded_tokens
            except Exception:
                pass

        # Strategy 4: Environment variable fallback
        if not loaded_tokens:
            import os

            env_token = os.environ.get("CLAUDE_CODE_TOKEN")
            if env_token:
                loaded_tokens = [env_token]
                logger.info(
                    "Loaded 1 token from CLAUDE_CODE_TOKEN environment variable"
                )
                return loaded_tokens

            env_tokens = os.environ.get("CLAUDE_CODE_TOKENS")
            if env_tokens:
                loaded_tokens = env_tokens.split(",")
                logger.info(
                    f"Loaded {len(loaded_tokens)} tokens from CLAUDE_CODE_TOKENS"
                )
                return loaded_tokens

        return loaded_tokens

    async def acquire_with_reservation(
        self, timeout: Optional[float] = None, task_id: Optional[str] = None
    ) -> TokenReservation:
        """
        Acquire a token with reservation and timeout

        Args:
            timeout: Reservation timeout in seconds (uses default if None)
            task_id: Optional task identifier for tracking

        Returns:
            TokenReservation object
        """
        if not self._initialized:
            await self.initialize()

        start_time = time.time()

        # Record queue depth for metrics
        if self.metrics:
            self.metrics.queue_depths.append(self.available_queue.qsize())

        # Get next available token from queue (lock-free)
        token_idx = await self.available_queue.get()

        # Create reservation
        reservation = TokenReservation(
            reservation_id=str(uuid.uuid4()),
            token_idx=token_idx,
            token=self.tokens[token_idx],
            reserved_at=time.time(),
            timeout=timeout or self.default_reservation_timeout,
            task_id=task_id,
        )

        # Update state
        self.token_states[token_idx] = TokenState.RESERVED
        self.reservations[reservation.reservation_id] = reservation
        self.token_to_reservation[token_idx] = reservation.reservation_id

        # Record metrics
        if self.metrics:
            acquisition_time = time.time() - start_time
            self.metrics.record_acquisition(acquisition_time)
            self.metrics.total_reservations += 1

        logger.debug(
            f"Reserved token {token_idx} with reservation {reservation.reservation_id}"
        )
        return reservation

    async def confirm_reservation(self, reservation_id: str) -> Tuple[str, int]:
        """
        Confirm a reservation and mark token as in use

        Args:
            reservation_id: Reservation to confirm

        Returns:
            Tuple of (token, token_idx)
        """
        if reservation_id not in self.reservations:
            raise ValueError(f"Invalid reservation ID: {reservation_id}")

        reservation = self.reservations[reservation_id]

        if reservation.is_expired:
            # Clean up expired reservation
            await self._release_reservation(reservation_id)
            raise TimeoutError(f"Reservation {reservation_id} has expired")

        # Mark as in use
        self.token_states[reservation.token_idx] = TokenState.IN_USE
        self.in_use.add(reservation.token_idx)  # Backward compatibility

        logger.debug(
            f"Confirmed reservation {reservation_id} for token {reservation.token_idx}"
        )
        return reservation.token, reservation.token_idx

    async def acquire_batch(
        self,
        count: int,
        timeout: Optional[float] = None,
        batch_id: Optional[str] = None,
    ) -> List[TokenReservation]:
        """
        Acquire multiple tokens as a batch for multi-agent tasks

        Args:
            count: Number of tokens to acquire
            timeout: Reservation timeout for all tokens
            batch_id: Optional batch identifier

        Returns:
            List of TokenReservation objects
        """
        if not self._initialized:
            await self.initialize()

        if count > len(self.tokens):
            raise ValueError(
                f"Cannot acquire {count} tokens, only {len(self.tokens)} available"
            )

        batch_id = batch_id or str(uuid.uuid4())
        reservations = []

        try:
            for _ in range(count):
                reservation = await self.acquire_with_reservation(timeout=timeout)
                reservation.batch_id = batch_id
                reservations.append(reservation)
                self.batch_allocations[batch_id].append(reservation.token_idx)

            if self.metrics:
                self.metrics.total_batch_allocations += 1

            logger.info(f"Allocated batch {batch_id} with {count} tokens")
            return reservations

        except Exception as e:
            # Rollback partial allocation on failure
            for res in reservations:
                await self._release_reservation(res.reservation_id)
            raise e

    async def release_batch(self, batch_id: str):
        """
        Release all tokens in a batch

        Args:
            batch_id: Batch identifier
        """
        if batch_id not in self.batch_allocations:
            logger.warning(f"Unknown batch ID: {batch_id}")
            return

        token_indices = self.batch_allocations[batch_id]
        for token_idx in token_indices:
            if token_idx in self.token_to_reservation:
                reservation_id = self.token_to_reservation[token_idx]
                await self._release_reservation(reservation_id)
            else:
                # Direct release if no reservation
                await self._release_token(token_idx)

        del self.batch_allocations[batch_id]
        logger.info(f"Released batch {batch_id}")

    async def _release_reservation(self, reservation_id: str):
        """Internal method to release a reservation"""
        if reservation_id not in self.reservations:
            return

        reservation = self.reservations[reservation_id]
        token_idx = reservation.token_idx

        # Clean up reservation
        del self.reservations[reservation_id]
        if token_idx in self.token_to_reservation:
            del self.token_to_reservation[token_idx]

        # Release token
        await self._release_token(token_idx)

    async def _release_token(self, token_idx: int):
        """Internal method to release a token back to the pool"""
        if self.token_states.get(token_idx) == TokenState.AVAILABLE:
            return  # Already available

        # Update state
        self.token_states[token_idx] = TokenState.AVAILABLE
        self.in_use.discard(token_idx)  # Backward compatibility

        # Return to available queue
        await self.available_queue.put(token_idx)

        if self.metrics:
            self.metrics.total_releases += 1

        logger.debug(f"Released token {token_idx}")

    async def _cleanup_expired_reservations(self):
        """Background task to clean up expired reservations"""
        while True:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds

                expired = []
                for res_id, reservation in self.reservations.items():
                    if reservation.is_expired:
                        expired.append(res_id)

                for res_id in expired:
                    logger.warning(f"Cleaning up expired reservation {res_id}")
                    await self._release_reservation(res_id)
                    if self.metrics:
                        self.metrics.total_timeouts += 1

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    # Backward compatibility methods
    async def acquire(self) -> Tuple[str, int]:
        """
        Original acquire method for backward compatibility
        Returns token immediately without reservation
        """
        if not self._initialized:
            await self.initialize()

        # Use reservation system but confirm immediately
        reservation = await self.acquire_with_reservation()
        return await self.confirm_reservation(reservation.reservation_id)

    def release(self, token_idx: int):
        """
        Original synchronous release for backward compatibility
        Creates a task to handle async release
        """
        asyncio.create_task(self._release_token(token_idx))
        logger.debug(f"Scheduled release of token {token_idx}")

    def size(self) -> int:
        """Get total number of tokens in pool"""
        return len(self.tokens)

    @property
    def available(self) -> int:
        """Get number of available tokens (backward compatibility)"""
        if not self._initialized:
            return len(self.tokens)
        return self.available_queue.qsize()

    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Get current metrics snapshot"""
        if not self.metrics:
            return None

        return {
            "total_tokens": len(self.tokens),
            "available_tokens": self.available_queue.qsize(),
            "reserved_tokens": len(self.reservations),
            "in_use_tokens": len(self.in_use),
            "total_acquisitions": self.metrics.total_acquisitions,
            "total_releases": self.metrics.total_releases,
            "total_reservations": self.metrics.total_reservations,
            "total_timeouts": self.metrics.total_timeouts,
            "total_batch_allocations": self.metrics.total_batch_allocations,
            "avg_acquisition_time": self.metrics.avg_acquisition_time,
            "avg_usage_duration": self.metrics.avg_usage_duration,
            "current_queue_depth": self.available_queue.qsize(),
        }


# Alias for drop-in replacement
TokenPool = EnhancedTokenPool
