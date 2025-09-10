"""Base adapter interface for ingestion pipeline."""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID

import structlog

from ..models.common import ContextItem

logger = structlog.get_logger(__name__)


class AdapterStatus(Enum):
    """Adapter operational status."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class BatchMode(Enum):
    """Batch processing modes."""

    STREAMING = "streaming"  # Process items as they come
    MICRO_BATCH = "micro_batch"  # Small batches (10-100 items)
    BATCH = "batch"  # Medium batches (100-1000 items)
    BULK = "bulk"  # Large batches (1000+ items)


@dataclass
class AdapterConfig:
    """Configuration for data source adapters."""

    # Identification
    adapter_id: str
    source_type: str
    version: str = "1.0"

    # Batch processing
    batch_mode: BatchMode = BatchMode.STREAMING
    batch_size: int = 100
    batch_timeout_seconds: int = 30

    # Rate limiting
    max_items_per_second: int = 1000
    max_concurrent_batches: int = 5

    # Retry configuration
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    retry_backoff_factor: float = 2.0

    # Health monitoring
    health_check_interval_seconds: int = 60
    error_threshold_count: int = 10
    error_threshold_window_seconds: int = 300

    # Data validation
    strict_validation: bool = True
    skip_duplicates: bool = True
    content_hash_check: bool = True

    # Transformation options
    generate_embeddings: bool = True
    generate_summaries: bool = False
    extract_relationships: bool = True

    # Source-specific configuration
    source_config: Dict[str, Any] = field(default_factory=dict)

    # Feature flags
    enabled_features: Set[str] = field(default_factory=set)
    disabled_features: Set[str] = field(default_factory=set)

    # Circuit breaker configuration
    circuit_breaker_threshold: int = 5  # Failures before opening circuit
    circuit_breaker_timeout_seconds: int = 60  # Time before retry
    circuit_breaker_reset_threshold: int = 3  # Successes to close circuit

    # Connection management
    connection_pool_size: int = 5
    connection_timeout_seconds: int = 30

    # Memory management
    max_memory_mb: int = 512
    memory_check_interval_seconds: int = 30


@dataclass
class AdapterMetrics:
    """Runtime metrics for adapters."""

    # Counters
    total_items_processed: int = 0
    total_items_failed: int = 0
    total_batches_processed: int = 0
    total_errors: int = 0

    # Rates (items per second)
    current_processing_rate: float = 0.0
    average_processing_rate: float = 0.0
    peak_processing_rate: float = 0.0

    # Timing (milliseconds)
    average_item_processing_time: float = 0.0
    average_batch_processing_time: float = 0.0
    total_processing_time: float = 0.0

    # Quality metrics
    duplicate_rate: float = 0.0
    validation_failure_rate: float = 0.0
    transformation_success_rate: float = 0.0

    # Resource usage
    current_memory_mb: float = 0.0
    peak_memory_mb: float = 0.0
    current_cpu_percent: float = 0.0

    # Status
    status: AdapterStatus = AdapterStatus.IDLE
    last_activity: Optional[datetime] = None
    last_error: Optional[str] = None
    uptime_seconds: float = 0.0


class ValidationError(Exception):
    """Data validation error."""

    pass


class TransformationError(Exception):
    """Data transformation error."""

    pass


class CircuitBreakerOpenError(Exception):
    """Circuit breaker is open, preventing operation."""

    pass


class RateLimitExceededError(Exception):
    """Rate limit has been exceeded."""

    pass


class BaseAdapter(ABC):
    """Abstract base class for all ingestion adapters.

    Defines the standard interface that all adapters must implement to
    participate in the ingestion pipeline.
    """

    def __init__(self, config: AdapterConfig):
        """Initialize adapter with configuration."""
        self.config = config
        self.metrics = AdapterMetrics()
        self._status = AdapterStatus.IDLE
        self._shutdown_event = asyncio.Event()
        self._error_count = 0
        self._start_time: Optional[datetime] = None

        # Circuit breaker state
        self._circuit_breaker_failures = 0
        self._circuit_breaker_last_failure: Optional[datetime] = None
        self._circuit_breaker_open = False
        self._circuit_breaker_success_count = 0

        # Rate limiting
        self._rate_limiter = asyncio.Semaphore(config.max_concurrent_batches)
        self._last_request_time: Optional[datetime] = None

        # Memory monitoring
        self._memory_check_task: Optional[asyncio.Task] = None
        self._last_memory_check: Optional[datetime] = None

        self.logger = logger.bind(
            adapter_id=config.adapter_id, source_type=config.source_type
        )

    @property
    def status(self) -> AdapterStatus:
        """Current adapter status."""
        return self._status

    @property
    def is_healthy(self) -> bool:
        """Check if adapter is in healthy state."""
        return (
            self._status not in {AdapterStatus.ERROR, AdapterStatus.SHUTDOWN}
            and self._error_count < self.config.error_threshold_count
        )

    # Abstract methods that must be implemented by concrete adapters

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize adapter resources.

        Called once before processing begins. Use this to set up connections,
        validate configuration, prepare caches, etc.

        Raises:
            Exception: If initialization fails
        """
        pass

    @abstractmethod
    async def fetch_items(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch raw items from the data source.

        Args:
            since: Fetch items created/modified after this timestamp
            until: Fetch items created/modified before this timestamp
            limit: Maximum number of items to fetch

        Yields:
            Raw item data dictionaries from the source system

        Raises:
            Exception: If fetching fails
        """
        pass

    @abstractmethod
    async def transform_item(self, raw_item: Dict[str, Any]) -> ContextItem:
        """Transform raw item into standardized ContextItem.

        Args:
            raw_item: Raw item data from fetch_items()

        Returns:
            Standardized ContextItem ready for database storage

        Raises:
            TransformationError: If transformation fails
            ValidationError: If validation fails
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up adapter resources.

        Called when adapter is shutting down. Use this to close connections,
        flush caches, save state, etc.
        """
        pass

    # Optional methods with default implementations

    async def validate_item(self, item: ContextItem) -> bool:
        """Validate transformed item.

        Args:
            item: ContextItem to validate

        Returns:
            True if item is valid, False otherwise

        Raises:
            ValidationError: If validation fails with error
        """
        if not item.source_type or not item.source_id:
            return False

        if not item.content and not item.title:
            return False

        return True

    async def detect_relationships(
        self, item: ContextItem, context_window: List[ContextItem]
    ) -> List[Tuple[str, UUID, float]]:
        """Detect relationships with other context items.

        Args:
            item: Current item being processed
            context_window: Recent items for relationship detection

        Returns:
            List of (relationship_type, target_item_id, confidence) tuples
        """
        return []

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text content.

        Args:
            text: Text to embed

        Returns:
            Vector embedding or None if generation fails
        """
        # Default implementation - override with actual embedding service
        return None

    async def generate_summary(self, content: str) -> Optional[str]:
        """Generate summary of content.

        Args:
            content: Content to summarize

        Returns:
            Generated summary or None if generation fails
        """
        # Default implementation - override with actual summarization
        return None

    # Pipeline integration methods

    async def start(self) -> None:
        """Start the adapter."""
        self.logger.info("Starting adapter")

        # Check circuit breaker before starting
        await self._check_circuit_breaker()

        self._status = AdapterStatus.RUNNING
        self._start_time = datetime.utcnow()

        # Start monitoring tasks
        await self._start_memory_monitoring()

        try:
            await self.initialize()
            self._record_circuit_breaker_success()
        except Exception as e:
            self._record_circuit_breaker_failure()
            self._record_error(e)
            raise

    async def stop(self) -> None:
        """Stop the adapter."""
        self.logger.info("Stopping adapter")
        self._status = AdapterStatus.SHUTDOWN
        self._shutdown_event.set()

        # Stop monitoring tasks
        await self._stop_memory_monitoring()

        try:
            await self.cleanup()
        except Exception as e:
            self.logger.error("Error during cleanup", error=str(e))

    async def pause(self) -> None:
        """Pause adapter processing."""
        self.logger.info("Pausing adapter")
        self._status = AdapterStatus.PAUSED

    async def resume(self) -> None:
        """Resume adapter processing."""
        self.logger.info("Resuming adapter")
        self._status = AdapterStatus.RUNNING

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check.

        Returns:
            Health status information
        """
        return {
            "adapter_id": self.config.adapter_id,
            "status": self._status.value,
            "is_healthy": self.is_healthy,
            "error_count": self._error_count,
            "uptime_seconds": self.metrics.uptime_seconds,
            "metrics": {
                "total_items_processed": self.metrics.total_items_processed,
                "total_items_failed": self.metrics.total_items_failed,
                "current_processing_rate": self.metrics.current_processing_rate,
                "average_processing_rate": self.metrics.average_processing_rate,
            },
        }

    # Error handling and metrics

    def _record_error(self, error: Exception, context: Dict[str, Any] = None):
        """Record an error for metrics and monitoring."""
        self._error_count += 1
        self.metrics.total_errors += 1
        self.metrics.last_error = str(error)

        self.logger.error(
            "Adapter error",
            error=str(error),
            error_type=type(error).__name__,
            context=context or {},
        )

        # Transition to error state if threshold exceeded
        if self._error_count >= self.config.error_threshold_count:
            self._status = AdapterStatus.ERROR

    def _record_success(self, processing_time_ms: float = 0.0):
        """Record successful item processing."""
        self.metrics.total_items_processed += 1

        if processing_time_ms > 0:
            # Update timing metrics
            total_time = self.metrics.total_processing_time
            total_items = self.metrics.total_items_processed

            self.metrics.total_processing_time = total_time + processing_time_ms
            self.metrics.average_item_processing_time = (
                self.metrics.total_processing_time / total_items
            )

        # Update uptime
        if self._start_time:
            self.metrics.uptime_seconds = (
                datetime.utcnow() - self._start_time
            ).total_seconds()

    def _calculate_rates(self, items_processed: int, time_elapsed_seconds: float):
        """Calculate processing rates."""
        if time_elapsed_seconds > 0:
            current_rate = items_processed / time_elapsed_seconds
            self.metrics.current_processing_rate = current_rate

            if current_rate > self.metrics.peak_processing_rate:
                self.metrics.peak_processing_rate = current_rate

            # Update average rate
            total_time = self.metrics.uptime_seconds
            total_items = self.metrics.total_items_processed

            if total_time > 0:
                self.metrics.average_processing_rate = total_items / total_time

    # Circuit breaker and resilience methods

    async def _check_circuit_breaker(self) -> None:
        """Check circuit breaker state and throw exception if open."""
        if not self._circuit_breaker_open:
            return

        # Check if timeout has passed
        if (
            self._circuit_breaker_last_failure
            and (datetime.utcnow() - self._circuit_breaker_last_failure).total_seconds()
            >= self.config.circuit_breaker_timeout_seconds
        ):
            # Move to half-open state
            self._circuit_breaker_open = False
            self._circuit_breaker_success_count = 0
            self.logger.info("Circuit breaker moving to half-open state")
            return

        raise CircuitBreakerOpenError(
            f"Circuit breaker is open for adapter {self.config.adapter_id}"
        )

    def _record_circuit_breaker_success(self):
        """Record successful operation for circuit breaker."""
        if self._circuit_breaker_open:
            # In half-open state, count successes
            self._circuit_breaker_success_count += 1
            if (
                self._circuit_breaker_success_count
                >= self.config.circuit_breaker_reset_threshold
            ):
                self._circuit_breaker_open = False
                self._circuit_breaker_failures = 0
                self._circuit_breaker_success_count = 0
                self.logger.info("Circuit breaker closed after successful operations")
        else:
            # Reset failure count on success
            self._circuit_breaker_failures = 0

    def _record_circuit_breaker_failure(self):
        """Record failed operation for circuit breaker."""
        self._circuit_breaker_failures += 1
        self._circuit_breaker_last_failure = datetime.utcnow()

        if self._circuit_breaker_failures >= self.config.circuit_breaker_threshold:
            self._circuit_breaker_open = True
            self._circuit_breaker_success_count = 0
            self.logger.warning(
                "Circuit breaker opened due to failures",
                failure_count=self._circuit_breaker_failures,
            )

    async def _check_rate_limit(self) -> None:
        """Check rate limiting and delay if necessary."""
        if self.config.max_items_per_second <= 0:
            return

        now = datetime.utcnow()

        if self._last_request_time:
            min_interval = 1.0 / self.config.max_items_per_second
            time_since_last = (now - self._last_request_time).total_seconds()

            if time_since_last < min_interval:
                delay = min_interval - time_since_last
                await asyncio.sleep(delay)

        self._last_request_time = datetime.utcnow()

    async def _check_memory_usage(self) -> None:
        """Check memory usage and warn if high."""
        try:
            import psutil

            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            self.metrics.current_memory_mb = memory_mb

            if memory_mb > self.metrics.peak_memory_mb:
                self.metrics.peak_memory_mb = memory_mb

            if memory_mb > self.config.max_memory_mb:
                self.logger.warning(
                    "High memory usage detected",
                    current_memory_mb=memory_mb,
                    max_memory_mb=self.config.max_memory_mb,
                )

        except ImportError:
            # psutil not available, skip memory checking
            pass
        except Exception as e:
            self.logger.error("Error checking memory usage", error=str(e))

    async def _start_memory_monitoring(self) -> None:
        """Start background memory monitoring task."""
        if self._memory_check_task:
            return

        async def memory_monitor():
            while not self._shutdown_event.is_set():
                try:
                    await self._check_memory_usage()
                    await asyncio.sleep(self.config.memory_check_interval_seconds)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error("Memory monitoring error", error=str(e))
                    await asyncio.sleep(self.config.memory_check_interval_seconds)

        self._memory_check_task = asyncio.create_task(memory_monitor())

    async def _stop_memory_monitoring(self) -> None:
        """Stop background memory monitoring task."""
        if self._memory_check_task:
            self._memory_check_task.cancel()
            try:
                await self._memory_check_task
            except asyncio.CancelledError:
                pass
            self._memory_check_task = None
